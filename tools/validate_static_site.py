"""Validate the deployable static site using only the Python standard library."""

from __future__ import annotations

import json
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
RETIRED_REDIRECTS = {
    "beer-server-comparison-2026": "/guides/cooling-methods/",
    "countertop-ice-maker-comparison-2026": "/p/clear-ice-ball-maker-comparison-2026/",
    "home-drinking-glass-comparison-2026": "/guides/cooling-methods/",
    "ice-pail-comparison-2026": "/guides/cooling-methods/",
    "prime-day-banshaku-cooling-2026": "/guides/cooling-methods/",
    "sodastream-comparison-2026": "/guides/cooling-methods/",
    "summer-beer-comparison-2026": "/",
    "whiskey-pump-comparison-2026": "/guides/reading-comparisons/",
    "yakitori-grill-comparison-2026": "/p/home-smoker-comparison-2026/",
}


class PageParser(HTMLParser):
    """Collect the small set of page facts needed for static validation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_depth = 0
        self.title_parts: list[str] = []
        self.h1_count = 0
        self.description = ""
        self.canonical = ""
        self.robots = ""
        self.links: list[tuple[str, str]] = []
        self.images_without_alt: list[str] = []
        self.images: list[dict[str, str]] = []
        self.json_ld_depth = 0
        self.json_ld_parts: list[str] = []
        self.json_ld_documents: list[dict[str, object]] = []

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
            tag == "meta"
            and attributes.get("name") == "robots"
            and attributes.get("content")
        ):
            self.robots = attributes["content"] or ""
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
            self.images.append(
                {key: value or "" for key, value in attrs if key}
            )
            alt = attributes.get("alt")
            if alt is None or not alt.strip():
                self.images_without_alt.append(attributes.get("src") or "<unknown>")
        elif tag == "script" and attributes.get("type") == "application/ld+json":
            self.json_ld_depth += 1
            self.json_ld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        elif tag == "script" and self.json_ld_depth:
            raw_json = "".join(self.json_ld_parts).strip()
            if raw_json:
                try:
                    parsed = json.loads(raw_json)
                except json.JSONDecodeError:
                    parsed = {"__invalid_json_ld__": raw_json}
                if isinstance(parsed, dict):
                    self.json_ld_documents.append(parsed)
            self.json_ld_depth -= 1
            self.json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)
        if self.json_ld_depth:
            self.json_ld_parts.append(data)


def schema_nodes(parser: PageParser) -> list[dict[str, object]]:
    """Flatten JSON-LD top-level documents and @graph entries."""
    nodes: list[dict[str, object]] = []
    for document in parser.json_ld_documents:
        graph = document.get("@graph")
        if isinstance(graph, list):
            nodes.extend(node for node in graph if isinstance(node, dict))
        else:
            nodes.append(document)
    return nodes


def node_has_type(node: dict[str, object], expected: str) -> bool:
    """Return whether a JSON-LD node declares a schema type."""
    value = node.get("@type")
    if isinstance(value, str):
        return value == expected
    return isinstance(value, list) and expected in value


def public_pages() -> list[Path]:
    """Return indexable site pages while excluding generated OGP HTML."""
    pages = [ROOT / "index.html"]
    pages.extend(
        path
        for path in ROOT.rglob("index.html")
        if path != ROOT / "index.html"
        and "assets" not in path.parts
        and not (
            len(path.parts) >= 3
            and path.parent.parent.name == "p"
            and path.parent.name in RETIRED_REDIRECTS
        )
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

        if label == "index.html" or label.startswith(("p/", "guides/")):
            required_robot_tokens = {
                "index",
                "follow",
                "max-image-preview:large",
                "max-snippet:-1",
                "max-video-preview:-1",
            }
            robot_tokens = {
                token.strip() for token in parser.robots.split(",") if token.strip()
            }
            missing_robot_tokens = required_robot_tokens - robot_tokens
            if missing_robot_tokens:
                errors.append(
                    f"{label}: robots meta lacks {sorted(missing_robot_tokens)}"
                )

        nodes = schema_nodes(parser)
        if any("__invalid_json_ld__" in document for document in parser.json_ld_documents):
            errors.append(f"{label}: JSON-LD is not valid JSON")
        if label == "index.html":
            for required_type in ("Organization", "WebSite", "CollectionPage"):
                if not any(node_has_type(node, required_type) for node in nodes):
                    errors.append(f"{label}: {required_type} JSON-LD is missing")

            entry_images = [
                image
                for image in parser.images
                if "entry-image" in image.get("class", "").split()
            ]
            if entry_images:
                for index, image in enumerate(entry_images):
                    if image.get("width") or image.get("height"):
                        errors.append(
                            f"index.html: entry image has fixed HTML dimensions: "
                            f"{image.get('src', '<unknown>')}"
                        )
                    if index == 0 and image.get("fetchpriority") != "high":
                        errors.append("index.html: featured image lacks fetchpriority=high")
                    if index > 0 and image.get("loading") != "lazy":
                        errors.append(
                            f"index.html: below-fold entry image is not lazy: "
                            f"{image.get('src', '<unknown>')}"
                        )

            for guide_path in (
                "/guides/cooling-methods/",
                "/guides/measure-before-buying/",
                "/guides/reading-comparisons/",
            ):
                if guide_path not in page_links:
                    errors.append(f"index.html: missing guide link {guide_path}")

        if label.startswith(("p/", "guides/")):
            article_nodes = [node for node in nodes if node_has_type(node, "Article")]
            if len(article_nodes) != 1:
                errors.append(
                    f"{label}: expected 1 Article JSON-LD node, found {len(article_nodes)}"
                )
            else:
                article = article_nodes[0]
                if article.get("headline") != parser.title:
                    errors.append(f"{label}: Article headline does not match title")
                if article.get("description") != parser.description:
                    errors.append(
                        f"{label}: Article description does not match meta description"
                    )
                if not article.get("datePublished") or not article.get("dateModified"):
                    errors.append(f"{label}: Article dates are incomplete")
                visible_dates = set(re.findall(r'<time datetime="([0-9-]+)"', text))
                for date_key in ("datePublished", "dateModified"):
                    date_value = article.get(date_key)
                    if isinstance(date_value, str) and date_value not in visible_dates:
                        errors.append(
                            f"{label}: {date_key} {date_value} is not visible in a time element"
                        )
            if not any(node_has_type(node, "BreadcrumbList") for node in nodes):
                errors.append(f"{label}: BreadcrumbList JSON-LD is missing")

            if label.startswith("p/"):
                self_path = urlsplit(expected_canonical).path
                related_paths = {
                    urlsplit(href).path
                    for href, _ in parser.links
                    if urlsplit(href).path.startswith("/p/")
                    and urlsplit(href).path != self_path
                }
                if len(related_paths) < 2:
                    errors.append(
                        f"{label}: expected at least 2 related comparison links, "
                        f"found {len(related_paths)}"
                    )
                if "<!-- Reader value:start -->" not in text:
                    errors.append(f"{label}: reader value block is missing")
            else:
                visible_text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", " ", text)
                visible_text = re.sub(r"\s+", "", visible_text)
                if len(visible_text) < 2200:
                    errors.append(f"{label}: guide text is unexpectedly short")

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
    sitemap_urls: dict[str, str] = {}
    for url_element in sitemap_root.findall("sm:url", namespace):
        loc = url_element.find("sm:loc", namespace)
        lastmod = url_element.find("sm:lastmod", namespace)
        if loc is not None and loc.text:
            sitemap_urls[loc.text.strip()] = (
                lastmod.text.strip() if lastmod is not None and lastmod.text else ""
            )
    expected_urls = {public_url(page) for page in pages}
    missing_from_sitemap = expected_urls - set(sitemap_urls)
    stale_in_sitemap = set(sitemap_urls) - expected_urls
    if missing_from_sitemap:
        errors.append(f"sitemap.xml: missing {sorted(missing_from_sitemap)}")
    if stale_in_sitemap:
        errors.append(f"sitemap.xml: stale URLs {sorted(stale_in_sitemap)}")
    missing_lastmod = {
        url
        for url in expected_urls & set(sitemap_urls)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", sitemap_urls[url])
    }
    if missing_lastmod:
        errors.append(f"sitemap.xml: missing valid lastmod for {sorted(missing_lastmod)}")

    redirects_path = ROOT / "_redirects"
    if not redirects_path.is_file():
        errors.append("_redirects: file is missing")
    else:
        redirects_text = redirects_path.read_text(encoding="utf-8")
        for slug, destination in RETIRED_REDIRECTS.items():
            rule = f"/p/{slug}/ {destination} 301"
            if rule not in redirects_text:
                errors.append(f"_redirects: missing rule {rule}")

    robots_text = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {BASE_URL}/sitemap.xml" not in robots_text:
        errors.append("robots.txt: canonical sitemap declaration is missing")
    for search_crawler in ("OAI-SearchBot", "Claude-SearchBot"):
        if f"User-agent: {search_crawler}" not in robots_text:
            errors.append(f"robots.txt: {search_crawler} rule is missing")

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
