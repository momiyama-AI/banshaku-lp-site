"""Apply deterministic search metadata to the static Banshaku site.

The site is hand-authored HTML, so this script keeps repeated Article, breadcrumb,
date, related-link, and image-loading markup consistent across every comparison.
It is intentionally idempotent and uses only the Python standard library.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://banshaku-lp-site.pages.dev"
PUBLISHER_ID = f"{SITE_URL}/#organization"

ARTICLE_DATES = {
    "beer-server-comparison-2026": ("2026-07-16", "2026-07-26"),
    "bottle-cooler-comparison-2026": ("2026-08-02", "2026-08-04"),
    "camp-can-holder-comparison-2026": ("2026-07-24", "2026-07-26"),
    "compact-air-fryer-comparison-2026": ("2026-07-29", "2026-07-29"),
    "countertop-ice-maker-comparison-2026": ("2026-07-19", "2026-07-26"),
    "electric-wine-opener-comparison-2026": ("2026-07-25", "2026-07-26"),
    "home-drinking-glass-comparison-2026": ("2026-07-13", "2026-07-26"),
    "home-smoker-comparison-2026": ("2026-07-22", "2026-07-26"),
    "ice-pail-comparison-2026": ("2026-07-18", "2026-07-26"),
    "prime-day-banshaku-cooling-2026": ("2026-07-11", "2026-07-26"),
    "second-fridge-comparison-2026": ("2026-07-20", "2026-07-26"),
    "shaved-ice-maker-comparison-2026": ("2026-07-28", "2026-07-28"),
    "sodastream-comparison-2026": ("2026-07-14", "2026-07-26"),
    "soft-cooler-comparison-2026": ("2026-07-26", "2026-07-26"),
    "summer-beer-comparison-2026": ("2026-07-27", "2026-07-27"),
    "whiskey-pump-comparison-2026": ("2026-07-12", "2026-07-26"),
    "wine-preservation-comparison-2026": ("2026-07-26", "2026-07-26"),
    "yakitori-grill-comparison-2026": ("2026-07-16", "2026-07-26"),
}

SHORT_TITLES = {
    "beer-server-comparison-2026": "缶ビールサーバー3タイプ比較",
    "bottle-cooler-comparison-2026": "家飲み用ボトルクーラー3製品比較",
    "camp-can-holder-comparison-2026": "保冷缶ホルダー3商品比較",
    "compact-air-fryer-comparison-2026": "コンパクトノンフライヤー3機種比較",
    "countertop-ice-maker-comparison-2026": "家庭用製氷機3機種比較",
    "electric-wine-opener-comparison-2026": "電動ワインオープナー3機種比較",
    "home-drinking-glass-comparison-2026": "家飲みグラス3タイプ比較",
    "home-smoker-comparison-2026": "家庭用燻製器3タイプ比較",
    "ice-pail-comparison-2026": "家飲みアイスペール3機種比較",
    "prime-day-banshaku-cooling-2026": "真夏日の晩酌グッズ3選",
    "second-fridge-comparison-2026": "晩酌用セカンド冷蔵庫3機種比較",
    "shaved-ice-maker-comparison-2026": "電動かき氷器3機種比較",
    "sodastream-comparison-2026": "ソーダストリーム全5機種比較",
    "soft-cooler-comparison-2026": "ソフトクーラー3商品比較",
    "summer-beer-comparison-2026": "2026年夏限定ビール4本予想比較",
    "whiskey-pump-comparison-2026": "電動ウイスキーポンプ3種比較",
    "wine-preservation-comparison-2026": "ワイン保存グッズ3方式比較",
    "yakitori-grill-comparison-2026": "卓上焼き鳥メーカー3種比較",
}

RELATED = {
    "beer-server-comparison-2026": ("camp-can-holder-comparison-2026", "summer-beer-comparison-2026", "home-drinking-glass-comparison-2026"),
    "bottle-cooler-comparison-2026": ("wine-preservation-comparison-2026", "electric-wine-opener-comparison-2026", "ice-pail-comparison-2026"),
    "camp-can-holder-comparison-2026": ("soft-cooler-comparison-2026", "summer-beer-comparison-2026", "beer-server-comparison-2026"),
    "compact-air-fryer-comparison-2026": ("home-smoker-comparison-2026", "yakitori-grill-comparison-2026", "second-fridge-comparison-2026"),
    "countertop-ice-maker-comparison-2026": ("ice-pail-comparison-2026", "shaved-ice-maker-comparison-2026", "sodastream-comparison-2026"),
    "electric-wine-opener-comparison-2026": ("wine-preservation-comparison-2026", "bottle-cooler-comparison-2026", "home-drinking-glass-comparison-2026"),
    "home-drinking-glass-comparison-2026": ("bottle-cooler-comparison-2026", "beer-server-comparison-2026", "whiskey-pump-comparison-2026"),
    "home-smoker-comparison-2026": ("compact-air-fryer-comparison-2026", "yakitori-grill-comparison-2026", "second-fridge-comparison-2026"),
    "ice-pail-comparison-2026": ("countertop-ice-maker-comparison-2026", "whiskey-pump-comparison-2026", "bottle-cooler-comparison-2026"),
    "prime-day-banshaku-cooling-2026": ("ice-pail-comparison-2026", "sodastream-comparison-2026", "beer-server-comparison-2026"),
    "second-fridge-comparison-2026": ("bottle-cooler-comparison-2026", "countertop-ice-maker-comparison-2026", "soft-cooler-comparison-2026"),
    "shaved-ice-maker-comparison-2026": ("countertop-ice-maker-comparison-2026", "sodastream-comparison-2026", "summer-beer-comparison-2026"),
    "sodastream-comparison-2026": ("countertop-ice-maker-comparison-2026", "whiskey-pump-comparison-2026", "prime-day-banshaku-cooling-2026"),
    "soft-cooler-comparison-2026": ("camp-can-holder-comparison-2026", "summer-beer-comparison-2026", "bottle-cooler-comparison-2026"),
    "summer-beer-comparison-2026": ("beer-server-comparison-2026", "camp-can-holder-comparison-2026", "soft-cooler-comparison-2026"),
    "whiskey-pump-comparison-2026": ("ice-pail-comparison-2026", "sodastream-comparison-2026", "home-drinking-glass-comparison-2026"),
    "wine-preservation-comparison-2026": ("electric-wine-opener-comparison-2026", "bottle-cooler-comparison-2026", "home-drinking-glass-comparison-2026"),
    "yakitori-grill-comparison-2026": ("home-smoker-comparison-2026", "compact-air-fryer-comparison-2026", "beer-server-comparison-2026"),
}

HOME_ORDER = (
    "bottle-cooler-comparison-2026",
    "compact-air-fryer-comparison-2026",
    "shaved-ice-maker-comparison-2026",
    "summer-beer-comparison-2026",
    "soft-cooler-comparison-2026",
    "wine-preservation-comparison-2026",
    "electric-wine-opener-comparison-2026",
    "camp-can-holder-comparison-2026",
    "home-smoker-comparison-2026",
    "second-fridge-comparison-2026",
    "countertop-ice-maker-comparison-2026",
    "beer-server-comparison-2026",
    "yakitori-grill-comparison-2026",
    "sodastream-comparison-2026",
    "home-drinking-glass-comparison-2026",
    "prime-day-banshaku-cooling-2026",
    "whiskey-pump-comparison-2026",
    "ice-pail-comparison-2026",
)

INFO_LASTMOD = {
    "/": "2026-08-04",
    "/about/": "2026-07-26",
    "/contact/": "2026-07-26",
    "/editorial-policy/": "2026-07-26",
    "/privacy/": "2026-07-26",
}

SEO_START = "  <!-- Search metadata:start -->"
SEO_END = "  <!-- Search metadata:end -->"
RELATED_START = "    <!-- Related comparisons:start -->"
RELATED_END = "    <!-- Related comparisons:end -->"
STYLESHEET_VERSION = "20260802-seo"


def extract(document: str, pattern: str) -> str:
    match = re.search(pattern, document, re.DOTALL)
    if not match:
        raise ValueError(f"Required HTML pattern not found: {pattern}")
    return html.unescape(match.group(1).strip())


def json_script(data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f'  <script type="application/ld+json">{payload}</script>'


def replace_search_block(document: str, block: str) -> str:
    document = re.sub(
        rf"{re.escape(SEO_START)}.*?{re.escape(SEO_END)}\n?",
        "",
        document,
        flags=re.DOTALL,
    )
    stylesheet = re.search(r'  <link rel="stylesheet"[^>]*>', document)
    if not stylesheet:
        raise ValueError("Stylesheet insertion point not found")
    return document[: stylesheet.start()] + block + "\n" + document[stylesheet.start() :]


def format_japanese_date(value: str) -> str:
    year, month, day = (int(part) for part in value.split("-"))
    return f"{year}年{month}月{day}日"


def article_graph(
    slug: str,
    title: str,
    description: str,
    image_url: str,
    published: str,
    modified: str,
) -> dict[str, object]:
    canonical = f"{SITE_URL}/p/{slug}/"
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": PUBLISHER_ID,
                "name": "晩酌ラボ",
                "url": f"{SITE_URL}/",
                "sameAs": ["https://x.com/banshaku_lab"],
            },
            {
                "@type": "Article",
                "@id": f"{canonical}#article",
                "headline": title,
                "description": description,
                "image": image_url.split("?", 1)[0],
                "datePublished": published,
                "dateModified": modified,
                "inLanguage": "ja-JP",
                "mainEntityOfPage": {"@id": canonical},
                "author": {
                    "@type": "Organization",
                    "name": "晩酌ラボ運営者",
                    "url": f"{SITE_URL}/about/",
                },
                "publisher": {"@id": PUBLISHER_ID},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "晩酌グッズ比較",
                        "item": f"{SITE_URL}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": SHORT_TITLES[slug],
                        "item": canonical,
                    },
                ],
            },
        ],
    }


def related_block(slug: str) -> str:
    links = "\n".join(
        f'        <li><a href="/p/{related_slug}/">{SHORT_TITLES[related_slug]}</a></li>'
        for related_slug in RELATED[slug]
    )
    return (
        f"{RELATED_START}\n"
        '    <section class="related-guides" aria-labelledby="related-guides-title">\n'
        '      <h2 id="related-guides-title">関連する晩酌グッズ比較</h2>\n'
        "      <p>用途が近い比較も、購入前の条件整理に役立ちます。</p>\n"
        '      <ul class="related-guides-list">\n'
        f"{links}\n"
        "      </ul>\n"
        "    </section>\n"
        f"{RELATED_END}"
    )


def update_article(slug: str) -> None:
    page = ROOT / "p" / slug / "index.html"
    document = page.read_text(encoding="utf-8")
    title = extract(document, r"<title>(.*?)</title>")
    description = extract(document, r'<meta name="description" content="([^"]*)">')
    image_url = extract(document, r'<meta property="og:image" content="([^"]*)">')
    published, modified = ARTICLE_DATES[slug]

    metadata = (
        f"{SEO_START}\n"
        '  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">\n'
        '  <meta property="og:site_name" content="晩酌ラボ">\n'
        + json_script(
            article_graph(slug, title, description, image_url, published, modified)
        )
        + f"\n{SEO_END}"
    )
    document = replace_search_block(document, metadata)

    date_parts = [
        f'公開：<time datetime="{published}">{format_japanese_date(published)}</time>'
    ]
    if modified != published:
        date_parts.append(
            f'更新：<time datetime="{modified}">{format_japanese_date(modified)}</time>'
        )
    editor_line = (
        '<p class="editor-meta">編集：<a href="/about/">晩酌ラボ運営者</a> ｜ '
        '<a href="/editorial-policy/">比較・編集方針</a> ｜ '
        + " ｜ ".join(date_parts)
        + "</p>"
    )
    document, count = re.subn(
        r'<p class="editor-meta">.*?</p>', editor_line, document, count=1
    )
    if count != 1:
        raise ValueError(f"{slug}: editor metadata insertion point not found")

    document = re.sub(
        rf"\n?{re.escape(RELATED_START)}.*?{re.escape(RELATED_END)}\n?",
        "\n",
        document,
        flags=re.DOTALL,
    )
    main_end = document.rfind("  </main>")
    if main_end == -1:
        raise ValueError(f"{slug}: main closing tag not found")
    document = (
        document[:main_end]
        + related_block(slug)
        + "\n"
        + document[main_end:]
    )
    page.write_text(document, encoding="utf-8", newline="\n")


def update_home() -> None:
    page = ROOT / "index.html"
    document = page.read_text(encoding="utf-8")
    item_list = []
    for position, slug in enumerate(HOME_ORDER, start=1):
        item_list.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": SHORT_TITLES[slug],
                "url": f"{SITE_URL}/p/{slug}/",
            }
        )
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": PUBLISHER_ID,
                "name": "晩酌ラボ",
                "url": f"{SITE_URL}/",
                "sameAs": ["https://x.com/banshaku_lab"],
            },
            {
                "@type": "WebSite",
                "@id": f"{SITE_URL}/#website",
                "url": f"{SITE_URL}/",
                "name": "晩酌ラボ",
                "description": extract(
                    document, r'<meta name="description" content="([^"]*)">'
                ),
                "inLanguage": "ja-JP",
                "publisher": {"@id": PUBLISHER_ID},
            },
            {
                "@type": "CollectionPage",
                "@id": f"{SITE_URL}/#webpage",
                "url": f"{SITE_URL}/",
                "name": extract(document, r"<title>(.*?)</title>"),
                "isPartOf": {"@id": f"{SITE_URL}/#website"},
                "mainEntity": {
                    "@type": "ItemList",
                    "numberOfItems": len(item_list),
                    "itemListElement": item_list,
                },
            },
        ],
    }
    metadata = (
        f"{SEO_START}\n"
        '  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">\n'
        '  <meta property="og:site_name" content="晩酌ラボ">\n'
        + json_script(graph)
        + f"\n{SEO_END}"
    )
    document = replace_search_block(document, metadata)

    image_index = 0

    def add_image_hints(match: re.Match[str]) -> str:
        nonlocal image_index
        tag = match.group(0)
        image_index += 1
        tag = re.sub(r'\s+(?:loading|decoding|fetchpriority|width|height)="[^"]*"', "", tag)
        if image_index == 1:
            hints = ' width="1200" height="675" decoding="async" fetchpriority="high"'
        else:
            hints = ' width="1200" height="675" loading="lazy" decoding="async"'
        return tag[:-1] + hints + ">"

    document = re.sub(
        r'<img class="entry-image"[^>]*>', add_image_hints, document
    )

    def describe_card_link(match: re.Match[str]) -> str:
        heading = html.unescape(re.sub(r"<[^>]+>", "", match.group("heading"))).strip()
        return (
            match.group("before")
            + f"{heading}を読む"
            + match.group("after")
        )

    document = re.sub(
        r'(?P<before><h3>(?P<heading>.*?)</h3>\s*<p>.*?</p>\s*<a class="button" href="[^"]+">)詳細を見る(?P<after></a>)',
        describe_card_link,
        document,
        flags=re.DOTALL,
    )
    document = document.replace(
        '<a class="button" href="/p/bottle-cooler-comparison-2026/">比較を見る</a>',
        '<a class="button" href="/p/bottle-cooler-comparison-2026/">卓上ボトルクーラー比較を読む</a>',
    )
    page.write_text(document, encoding="utf-8", newline="\n")


def update_sitemap() -> None:
    entries = list(INFO_LASTMOD.items())
    entries[4:4] = [
        (f"/p/{slug}/", modified)
        for slug, (_, modified) in ARTICLE_DATES.items()
    ]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, lastmod in entries:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{SITE_URL}{path}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_stylesheet_version() -> None:
    pages = [ROOT / "index.html", ROOT / "404.html"]
    pages.extend(ROOT.glob("*/index.html"))
    pages.extend((ROOT / "p").glob("*/index.html"))
    for page in pages:
        document = page.read_text(encoding="utf-8")
        document = re.sub(
            r'/assets/site-info\.css\?v=[^"]+',
            f"/assets/site-info.css?v={STYLESHEET_VERSION}",
            document,
        )
        page.write_text(document, encoding="utf-8", newline="\n")


def main() -> None:
    if (
        set(ARTICLE_DATES) != set(SHORT_TITLES)
        or set(ARTICLE_DATES) != set(RELATED)
        or set(ARTICLE_DATES) != set(HOME_ORDER)
    ):
        raise ValueError("Article metadata maps are out of sync")
    update_home()
    for slug in ARTICLE_DATES:
        update_article(slug)
    update_sitemap()
    update_stylesheet_version()
    print(f"Search markup applied to {len(ARTICLE_DATES)} comparison pages and home.")


if __name__ == "__main__":
    main()
