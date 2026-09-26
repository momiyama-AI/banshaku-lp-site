"""Check the 18 generated pages, OGPs, static content, links, and optional dist."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image
from build import BASE_URL, ROOT, TITLE, FOOTER, read_data, recommend
from package_site import is_public


class Document(HTMLParser):
    """Collect semantic HTML metadata without depending on a browser."""
    def __init__(self, markup: str) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.canonical: list[str] = []
        self.tags: list[tuple[str, dict]] = []
        self.text: list[str] = []
        self.title: list[str] = []
        self.in_title = False
        self.feed(markup)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        values = dict(attrs)
        self.tags.append((tag, values))
        if tag == "meta":
            self.meta[values.get("name", values.get("property", ""))] = values.get("content", "")
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical.append(values["href"])
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.in_title:
            self.title.append(data)


def check(dist: bool = False) -> None:
    """Fail on an incorrect meta tag, missing image, or tool leaked to dist."""
    data, _, recipes = read_data()
    root = ROOT / "dist" if dist else ROOT
    site = root / "shindan"
    files = sorted(site.rglob("*.html"))
    assert len(files) == 18, f"Expected 18 pages, found {len(files)}"
    assert len(list((site / "og").glob("*.png"))) == 17
    for file in files:
        markup = file.read_text(encoding="utf-8")
        doc = Document(markup)
        visible = "".join(doc.text)
        assert doc.title and len(doc.canonical) == 1, file
        expected = BASE_URL + "/" + file.relative_to(root).parent.as_posix() + "/"
        assert doc.canonical[0] == expected, file
        for required in ("description", "og:title", "og:description", "og:image", "twitter:card"):
            assert doc.meta.get(required), (file, required)
        assert doc.meta["twitter:card"] == "summary_large_image"
        assert doc.meta["og:url"] == expected
        image = urlparse(doc.meta["og:image"])
        assert image.scheme == "https" and image.netloc == urlparse(BASE_URL).netloc
        assert not image.query and not image.fragment
        assert image.path.startswith("/shindan/og/") and image.path.endswith(".png")
        with Image.open(root / image.path.lstrip("/")) as picture:
            assert picture.format == "PNG" and picture.size == (1200, 630), file
            picture.verify()
        assert FOOTER in visible and "運営：晩酌ラボ（" in visible
        assert "MBTI" not in markup
        for tag, attrs in doc.tags:
            # No runtime CDN, fonts, ad scripts, iframes, or cross-origin data collection.
            if tag in ("script", "img", "iframe") and attrs.get("src"):
                assert attrs["src"].startswith("/shindan/"), (file, attrs)
            if tag == "link" and attrs.get("rel") == "stylesheet":
                assert attrs["href"] == "/shindan/assets/style.css"
            if tag == "a" and attrs.get("target") == "_blank":
                assert set(attrs.get("rel", "").split()) >= {"noopener", "noreferrer"}
            if attrs.get("href", "").startswith("/shindan/"):
                target = root / attrs["href"].split("#")[0].lstrip("/")
                assert target.is_file() or (target / "index.html").is_file(), (file, target)
        if file.parent.name not in ("shindan", "types"):
            code = file.parent.name.upper()
            item = next(t for t in data["types"] if t["code"] == code)
            assert "".join(doc.title) == f'{item["name"]}（{code}）｜{TITLE}｜晩酌ラボ'
            group = next(g for g in data["groups"] if code.startswith(g["code"]))
            for value in [item["name"], item["line"], code, group["name"], group["drinks"]]:
                assert value in visible, (file, value)
            opposite = "".join(next(x for x in a["letters"] if x != code[i]) for i, a in enumerate(data["axes"]))
            partner = next(t for t in data["types"] if t["code"] == opposite)
            assert partner["name"] in visible
            for recipe in recommend(code, recipes, data["axes"]):
                assert recipe["name"] in visible
            ids = {a["id"]: a for _, a in doc.tags if a.get("id")}
            assert "hidden" in ids["personal-result"]
            assert "hidden" in ids["share-more"] and "hidden" in ids["threads-profile"]
            shared = parse_qs(urlparse(ids["share-x"]["href"]).query)
            assert shared["url"] == [expected] and "#" not in shared["url"][0]
    if dist:
        assert not (root / "tools").exists()
        assert not any(root.rglob("*.ttf")) and not any(root.rglob("*.py"))
        for path in root.rglob("*"):
            if path.is_file() and path.name != ".gitignore":
                relative = path.relative_to(root).as_posix()
                assert is_public(relative), relative
                assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256((ROOT / relative).read_bytes()).digest(), relative
    print("PASS: 18 pages, metadata/static content/links, 17 PNGs (1200x630)" +
          ("; dist has no tools/fonts and all public bytes match the source." if dist else "."))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", action="store_true")
    check(parser.parse_args().dist)
