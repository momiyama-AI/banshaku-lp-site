"""Validate the deployable static site using only the Python standard library."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://banshaku-lp-site.pages.dev"
REQUIRED_INFO_LINKS = {
    "/about/",
    "/contact/",
    "/editorial-policy/",
    "/privacy/",
}
AMAZON_DISCLOSURE = (
    "Amazonのアソシエイトとして、晩酌ラボは適格販売により収入を得ています。"
)


class PageParser(HTMLParser):
    """Collect the small set of page facts needed for static validation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_depth = 0
        self.title_parts: list[str] = []
        self.h1_count = 0
        self.description = ""
        self.canonical = ""
        self.links: list[tuple[str, str]] = []
        self.images_without_alt: list[str] = []

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if tag == "title":
            self.title_depth += 1
        elif tag == "h1":
            self.h1_count += 1
        elif (
            tag == "meta"
            and attributes.get("name") == "description"
            and attributes.get("content")
        ):
            self.description = attributes["content"] or ""
        elif (
            tag == "link"
            and attributes.get("rel") == "canonical"
            and attributes.get("href")
        ):
            self.canonical = attributes["href"] or ""
        elif tag == "a" and attributes.get("href"):
            self.links.append(
                (attributes["href"] or "", attributes.get("rel") or "")
            )
        elif tag == "img":
            alt = attributes.get("alt")
            if alt is None or not alt.strip():
                self.images_without_alt.append(attributes.get("src") or "<unknown>")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)


def public_pages() -> list[Path]:
    """Return indexable site pages while excluding generated OGP HTML."""
    pages = [ROOT / "index.html"]
    pages.extend(
        path
        for path in ROOT.rglob("index.html")
        if path != ROOT / "index.html" and "assets" not in path.parts
    )
    return sorted(pages)


def public_url(path: Path) -> str:
    """Map a local index page to its canonical production URL."""
    relative = path.relative_to(ROOT).as_posix()
    if relative == "index.html":
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{relative.removesuffix('index.html')}"


def internal_target_exists(href: str) -> bool:
    """Check whether a root-relative link resolves to a deployable local target."""
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return True
    path = parsed.path
    if path == "/":
        return (ROOT / "index.html").is_file()
    candidate = ROOT / path.lstrip("/")
    if path.endswith("/"):
        candidate = candidate / "index.html"
    return candidate.is_file()


def validate() -> list[str]:
    """Return all validation errors without stopping after the first failure."""
    errors: list[str] = []
    pages = public_pages()
    seen_titles: dict[str, Path] = {}
    seen_canonicals: dict[str, Path] = {}

    for page in pages:
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        label = page.relative_to(ROOT).as_posix()

        if not parser.title:
            errors.append(f"{label}: title is missing")
        elif parser.title in seen_titles:
            errors.append(
                f"{label}: title duplicates {seen_titles[parser.title].relative_to(ROOT)}"
            )
        else:
            seen_titles[parser.title] = page

        if not parser.description.strip():
            errors.append(f"{label}: meta description is missing")
        if parser.h1_count != 1:
            errors.append(f"{label}: expected 1 h1, found {parser.h1_count}")

        expected_canonical = public_url(page)
        if parser.canonical != expected_canonical:
            errors.append(
                f"{label}: canonical is {parser.canonical!r}, expected {expected_canonical!r}"
            )
        elif parser.canonical in seen_canonicals:
            errors.append(
                f"{label}: canonical duplicates "
                f"{seen_canonicals[parser.canonical].relative_to(ROOT)}"
            )
        else:
            seen_canonicals[parser.canonical] = page

        page_links = {href for href, _ in parser.links}
        missing_info = REQUIRED_INFO_LINKS - page_links
        if missing_info:
            errors.append(
                f"{label}: missing site information links {sorted(missing_info)}"
            )

        for href, rel in parser.links:
            if not internal_target_exists(href):
                errors.append(f"{label}: broken internal link {href}")
            if (
                (
                    ("amazon.co.jp" in href and "tag=" in urlsplit(href).query)
                    or "hb.afl.rakuten.co.jp" in href
                )
                and "sponsored" not in rel.split()
            ):
                errors.append(f"{label}: affiliate link lacks rel=sponsored: {href}")

        for src in parser.images_without_alt:
            errors.append(f"{label}: image lacks alt text: {src}")

        if re.search(r"\[(?:TODO|運営者名|連絡先|入力|要確認)[^\]]*\]", text):
            errors.append(f"{label}: placeholder text remains")
        if "/assets/site-info.css" not in text:
            errors.append(f"{label}: shared site-information stylesheet is missing")
        if AMAZON_DISCLOSURE not in text:
            errors.append(f"{label}: Amazon Associates disclosure is missing")

    og_entry_pages = sorted((ROOT / "assets" / "og").glob("*-entry.html"))
    for page in og_entry_pages:
        text = page.read_text(encoding="utf-8")
        if not re.search(
            r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex',
            text,
            re.IGNORECASE,
        ):
            errors.append(
                f"{page.relative_to(ROOT).as_posix()}: generated OGP page lacks noindex"
            )

    not_found_text = (ROOT / "404.html").read_text(encoding="utf-8")
    if 'name="robots" content="noindex' not in not_found_text:
        errors.append("404.html: noindex is missing")
    for info_link in REQUIRED_INFO_LINKS:
        if f'href="{info_link}"' not in not_found_text:
            errors.append(f"404.html: missing site information link {info_link}")

    sitemap_path = ROOT / "sitemap.xml"
    sitemap_root = ET.parse(sitemap_path).getroot()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = {
        element.text.strip()
        for element in sitemap_root.findall("sm:url/sm:loc", namespace)
        if element.text
    }
    expected_urls = {public_url(page) for page in pages}
    missing_from_sitemap = expected_urls - sitemap_urls
    stale_in_sitemap = sitemap_urls - expected_urls
    if missing_from_sitemap:
        errors.append(f"sitemap.xml: missing {sorted(missing_from_sitemap)}")
    if stale_in_sitemap:
        errors.append(f"sitemap.xml: stale URLs {sorted(stale_in_sitemap)}")

    robots_text = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {BASE_URL}/sitemap.xml" not in robots_text:
        errors.append("robots.txt: canonical sitemap declaration is missing")

    return errors


def main() -> int:
    """Print a concise result suitable for CI or local verification."""
    errors = validate()
    if errors:
        print(f"Static site validation failed with {len(errors)} issue(s):")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Static site validation passed for {len(public_pages())} pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
