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
    "bottle-cooler-comparison-2026": ("2026-08-02", "2026-08-07"),
    "camp-can-holder-comparison-2026": ("2026-07-24", "2026-08-07"),
    "clear-ice-ball-maker-comparison-2026": ("2026-08-06", "2026-08-07"),
    "compact-air-fryer-comparison-2026": ("2026-07-29", "2026-08-07"),
    "countertop-ice-maker-comparison-2026": ("2026-07-19", "2026-07-26"),
    "electric-wine-opener-comparison-2026": ("2026-07-25", "2026-08-07"),
    "home-drinking-glass-comparison-2026": ("2026-07-13", "2026-07-26"),
    "home-smoker-comparison-2026": ("2026-07-22", "2026-08-07"),
    "ice-pail-comparison-2026": ("2026-07-18", "2026-07-26"),
    "prime-day-banshaku-cooling-2026": ("2026-07-11", "2026-07-26"),
    "second-fridge-comparison-2026": ("2026-07-20", "2026-08-07"),
    "shaved-ice-maker-comparison-2026": ("2026-07-28", "2026-08-07"),
    "sodastream-comparison-2026": ("2026-07-14", "2026-07-26"),
    "soft-cooler-comparison-2026": ("2026-07-26", "2026-08-07"),
    "summer-beer-comparison-2026": ("2026-07-27", "2026-07-27"),
    "whiskey-pump-comparison-2026": ("2026-07-12", "2026-07-26"),
    "wine-preservation-comparison-2026": ("2026-07-26", "2026-08-07"),
    "yakitori-grill-comparison-2026": ("2026-07-16", "2026-07-26"),
}

SHORT_TITLES = {
    "beer-server-comparison-2026": "缶ビールサーバー3タイプ比較",
    "bottle-cooler-comparison-2026": "家飲み用ボトルクーラー3製品比較",
    "camp-can-holder-comparison-2026": "保冷缶ホルダー3商品比較",
    "clear-ice-ball-maker-comparison-2026": "透明な丸氷メーカー3製品比較",
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
    "bottle-cooler-comparison-2026": ("wine-preservation-comparison-2026", "second-fridge-comparison-2026"),
    "camp-can-holder-comparison-2026": ("soft-cooler-comparison-2026", "bottle-cooler-comparison-2026"),
    "clear-ice-ball-maker-comparison-2026": ("shaved-ice-maker-comparison-2026", "bottle-cooler-comparison-2026"),
    "compact-air-fryer-comparison-2026": ("home-smoker-comparison-2026", "second-fridge-comparison-2026"),
    "countertop-ice-maker-comparison-2026": ("ice-pail-comparison-2026", "shaved-ice-maker-comparison-2026", "sodastream-comparison-2026"),
    "electric-wine-opener-comparison-2026": ("wine-preservation-comparison-2026", "bottle-cooler-comparison-2026"),
    "home-drinking-glass-comparison-2026": ("bottle-cooler-comparison-2026", "beer-server-comparison-2026", "whiskey-pump-comparison-2026"),
    "home-smoker-comparison-2026": ("compact-air-fryer-comparison-2026", "second-fridge-comparison-2026"),
    "ice-pail-comparison-2026": ("countertop-ice-maker-comparison-2026", "whiskey-pump-comparison-2026", "bottle-cooler-comparison-2026"),
    "prime-day-banshaku-cooling-2026": ("ice-pail-comparison-2026", "sodastream-comparison-2026", "beer-server-comparison-2026"),
    "second-fridge-comparison-2026": ("bottle-cooler-comparison-2026", "compact-air-fryer-comparison-2026"),
    "shaved-ice-maker-comparison-2026": ("clear-ice-ball-maker-comparison-2026", "bottle-cooler-comparison-2026"),
    "sodastream-comparison-2026": ("countertop-ice-maker-comparison-2026", "whiskey-pump-comparison-2026", "prime-day-banshaku-cooling-2026"),
    "soft-cooler-comparison-2026": ("camp-can-holder-comparison-2026", "bottle-cooler-comparison-2026"),
    "summer-beer-comparison-2026": ("beer-server-comparison-2026", "camp-can-holder-comparison-2026", "soft-cooler-comparison-2026"),
    "whiskey-pump-comparison-2026": ("ice-pail-comparison-2026", "sodastream-comparison-2026", "home-drinking-glass-comparison-2026"),
    "wine-preservation-comparison-2026": ("electric-wine-opener-comparison-2026", "bottle-cooler-comparison-2026"),
    "yakitori-grill-comparison-2026": ("home-smoker-comparison-2026", "compact-air-fryer-comparison-2026", "beer-server-comparison-2026"),
}

HOME_ORDER = (
    "bottle-cooler-comparison-2026",
    "clear-ice-ball-maker-comparison-2026",
    "compact-air-fryer-comparison-2026",
    "shaved-ice-maker-comparison-2026",
    "soft-cooler-comparison-2026",
    "wine-preservation-comparison-2026",
    "electric-wine-opener-comparison-2026",
    "camp-can-holder-comparison-2026",
    "home-smoker-comparison-2026",
    "second-fridge-comparison-2026",
)

GUIDE_PAGES = {
    "/guides/cooling-methods/": ("冷やす・保つ・保管するの違い", "2026-08-07"),
    "/guides/measure-before-buying/": ("家飲み道具の購入前寸法チェック", "2026-08-07"),
    "/guides/reading-comparisons/": ("比較記事の根拠を見分ける読み方", "2026-08-07"),
}

GUIDE_RELATED = {
    "bottle-cooler-comparison-2026": ("/guides/cooling-methods/", "冷やす・保つ・保管するの違い"),
    "camp-can-holder-comparison-2026": ("/guides/measure-before-buying/", "購入前の寸法チェック"),
    "clear-ice-ball-maker-comparison-2026": ("/guides/cooling-methods/", "冷やす・保つ・保管するの違い"),
    "compact-air-fryer-comparison-2026": ("/guides/measure-before-buying/", "購入前の寸法チェック"),
    "electric-wine-opener-comparison-2026": ("/guides/reading-comparisons/", "比較記事の根拠を見分ける"),
    "home-smoker-comparison-2026": ("/guides/measure-before-buying/", "購入前の寸法チェック"),
    "second-fridge-comparison-2026": ("/guides/measure-before-buying/", "購入前の寸法チェック"),
    "shaved-ice-maker-comparison-2026": ("/guides/measure-before-buying/", "購入前の寸法チェック"),
    "soft-cooler-comparison-2026": ("/guides/cooling-methods/", "冷やす・保つ・保管するの違い"),
    "wine-preservation-comparison-2026": ("/guides/reading-comparisons/", "比較記事の根拠を見分ける"),
}

PRE_PURCHASE_CHECKS = {
    "bottle-cooler-comparison-2026": (
        ("よく飲む瓶を測る", "容量表示だけでなく、瓶の最も太い部分の直径と高さを測り、メーカーの対応寸法と照合します。"),
        ("冷やすか保つか決める", "常温から冷やしたいのか、冷蔵庫から出した後の温度上昇を抑えたいのかを先に分けます。"),
        ("準備と片付けを決める", "氷と排水、事前冷凍、筒形収納のうち、毎回続けられる条件を選びます。"),
    ),
    "camp-can-holder-comparison-2026": (
        ("使う缶サイズを固定する", "350ml・500mlなど、実際に買う缶とメーカーの対応サイズを照合します。"),
        ("総重量で考える", "本体だけでなく、缶や持ち物を合わせて歩く距離に無理がないか確認します。"),
        ("カップ兼用の条件を見る", "直接飲料を入れられるか、フタや洗浄方法が用途に合うかを取扱説明書で確認します。"),
    ),
    "clear-ice-ball-maker-comparison-2026": (
        ("グラスの内径を測る", "完成する氷の直径よりグラスの口が大きいか、最も狭い部分も含めて確認します。"),
        ("冷凍庫の空きを測る", "製氷中に水平を保てる幅・奥行・高さと、取り出すための手の余白を確保します。"),
        ("1回の個数を数える", "必要な杯数と製氷時間から、前日準備で足りるかを判断します。"),
    ),
    "compact-air-fryer-comparison-2026": (
        ("置き場所と排気を確認する", "本体外寸に、取扱説明書が示す周囲の余白とバスケットを引き出す前面スペースを足します。"),
        ("普段の一皿を想定する", "容量の数字だけでなく、よく温め直す食品が重ならずに入るかを確認します。"),
        ("洗う部品を数える", "バスケット、網、トレーなど毎回外す部品と、食洗機対応の有無を確認します。"),
    ),
    "electric-wine-opener-comparison-2026": (
        ("対象外コルクを確認する", "合成コルク、古いコルク、特殊形状など、メーカーが使用を案内しない条件を先に確認します。"),
        ("電源の運用を決める", "電池交換か充電か、保管場所の近くで無理なく管理できる方式を選びます。"),
        ("握り方と高さを確認する", "ボトル上で本体を垂直に保てるか、収納時の長さと重量も確認します。"),
    ),
    "home-smoker-comparison-2026": (
        ("使用場所を説明書で確認する", "屋内・屋外、換気、熱源、周囲の可燃物など、メーカーが指定する条件を満たす場所だけで検討します。"),
        ("加熱するか香り付けか決める", "食材を加熱する器具と、加熱済み食材へ香りを付ける器具を混同しません。"),
        ("洗う部品と煙の後処理を見る", "脂が触れる部品、チップ受け、フタ、保管前の乾燥まで含めて続けられるか確認します。"),
    ),
    "second-fridge-comparison-2026": (
        ("本体＋必要余白を測る", "外寸だけでなく、放熱、扉、コード、霜取りや掃除に必要な余白を取扱説明書から足します。"),
        ("入れる容器を並べる", "庫内容量の数字ではなく、瓶を立てる高さ、棚位置、扉ポケットの形を確認します。"),
        ("電源と運転音の場所を決める", "コンセント、アース、延長コードの可否と、就寝・作業場所からの距離を確認します。"),
    ),
    "shaved-ice-maker-comparison-2026": (
        ("使える氷を確認する", "家庭の角氷、付属カップの氷、冷凍フルーツなど、メーカーが明記する対応範囲だけで選びます。"),
        ("冷凍庫の準備を見積もる", "専用カップの個数と置き場所、凍らせる時間を普段の予定に合わせます。"),
        ("分解と乾燥を確認する", "刃に触れずに外せる部品、洗える範囲、乾燥させる場所を説明書で確認します。"),
    ),
    "soft-cooler-comparison-2026": (
        ("中身を実物で並べる", "飲み物、食品、保冷剤を並べ、必要容量と形を決めてから製品サイズを見ます。"),
        ("持ち運び重量を足す", "本体重量だけでなく、中身と保冷剤を合わせ、移動距離に無理がないか確認します。"),
        ("帰宅後の乾燥場所を決める", "内側を拭き、開いた状態で乾かし、折りたたんで収納できる場所を確保します。"),
    ),
    "wine-preservation-comparison-2026": (
        ("次に飲む日を決める", "何日後に残りを飲むかを先に決め、必要以上に高い保存方式を選ばないようにします。"),
        ("継続費用を分ける", "本体価格と、ガス・栓・電池など使うたびに必要な費用を分けて確認します。"),
        ("ボトルと保管場所を確認する", "口径や形状の対応、栓を付けた状態の高さ、冷蔵庫内での置き方を確認します。"),
    ),
}

EVIDENCE_LIMITS = {
    "bottle-cooler-comparison-2026": ("メーカー6ページと販売情報", "当サイトによる冷却時間・保冷時間・結露の実測"),
    "camp-can-holder-comparison-2026": ("メーカー3ページと対応缶・構造", "当サイトによる保冷温度・飲み口・携帯性の実測"),
    "clear-ice-ball-maker-comparison-2026": ("メーカー6ページと公式価格", "当サイトによる透明度・溶け方・味の実測"),
    "compact-air-fryer-comparison-2026": ("メーカー4ページと公開仕様", "当サイトによる仕上がり・所要時間・騒音の実測"),
    "electric-wine-opener-comparison-2026": ("メーカー3ページと公開仕様", "当サイトによる開栓成功率・握りやすさ・騒音の実測"),
    "home-smoker-comparison-2026": ("メーカー4ページと公開仕様", "当サイトによる煙量・香り・調理時間の実測"),
    "second-fridge-comparison-2026": ("メーカー4ページと公開仕様", "当サイトによる運転音・庫内温度・消費電力の実測"),
    "shaved-ice-maker-comparison-2026": ("メーカー6ページと販売情報", "当サイトによる食感・速度・騒音の実測"),
    "soft-cooler-comparison-2026": ("メーカー4ページと公開仕様", "当サイトによる同条件の保冷時間・防水性・携帯性の実測"),
    "wine-preservation-comparison-2026": ("メーカー5ページと公開仕様", "当サイトによる保存後の香味・操作性・ガス消費量の実測"),
}

INFO_LASTMOD = {
    "/": "2026-08-07",
    "/about/": "2026-08-07",
    "/contact/": "2026-07-26",
    "/editorial-policy/": "2026-08-07",
    "/privacy/": "2026-07-26",
}

SEO_START = "  <!-- Search metadata:start -->"
SEO_END = "  <!-- Search metadata:end -->"
RELATED_START = "    <!-- Related comparisons:start -->"
RELATED_END = "    <!-- Related comparisons:end -->"
QUALITY_START = "    <!-- Reader value:start -->"
QUALITY_END = "    <!-- Reader value:end -->"
STYLESHEET_VERSION = "20260807-quality"


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
                    "name": "晩酌ラボ編集部",
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
    guide_path, guide_title = GUIDE_RELATED[slug]
    links += f'\n        <li><a href="{guide_path}">{guide_title}</a></li>'
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


def quality_block(slug: str) -> str:
    checks = "\n".join(
        (
            "        <li>"
            f"<strong>{html.escape(title)}</strong>"
            f"{html.escape(description)}"
            "</li>"
        )
        for title, description in PRE_PURCHASE_CHECKS[slug]
    )
    confirmed, not_confirmed = EVIDENCE_LIMITS[slug]
    guide_path, guide_title = GUIDE_RELATED[slug]
    return (
        f"{QUALITY_START}\n"
        '    <section class="reader-checklist" aria-labelledby="reader-checklist-title">\n'
        '      <p class="reader-eyebrow">Before You Buy</p>\n'
        '      <h2 id="reader-checklist-title">販売ページを開く前に、手元で確認する3項目</h2>\n'
        "      <p>商品を買う前に、自分の容器、置き場所、準備と片付けへ置き換えます。"
        "3項目のどれかを確認できない場合は、購入を急がずメーカー情報を確認してください。</p>\n"
        '      <ol class="reader-checklist-grid">\n'
        f"{checks}\n"
        "      </ol>\n"
        '      <div class="evidence-scope">\n'
        "        <h3>この記事の検証範囲</h3>\n"
        "        <dl>\n"
        f"          <dt>確認した情報</dt><dd>{html.escape(confirmed)}</dd>\n"
        f"          <dt>確認していない情報</dt><dd>{html.escape(not_confirmed)}</dd>\n"
        "          <dt>評価の種類</dt><dd>公開仕様を生活場面へ当てはめた編集判断</dd>\n"
        "        </dl>\n"
        "      </div>\n"
        f'      <p class="reader-guide-link">判断の根拠を見分ける方法は、<a href="{guide_path}">{guide_title}</a>'
        'と<a href="/guides/reading-comparisons/">比較記事の検証記録</a>で確認できます。</p>\n'
        "    </section>\n"
        f"{QUALITY_END}"
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

    nav = (
        '    <div class="site-nav-inner">\n'
        '      <a class="brand-link" href="/">晩酌ラボ</a>\n'
        '      <div class="site-nav-links">\n'
        '        <a href="/#guides">選び方ガイド</a>\n'
        '        <a href="/#comparisons">比較記事</a>\n'
        '        <a href="/about/">運営者情報</a>\n'
        '      </div>\n'
        '    </div>'
    )
    document, nav_count = re.subn(
        r'    <div class="site-nav-inner">.*?</div>\s*</nav>',
        nav + "\n  </nav>",
        document,
        count=1,
        flags=re.DOTALL,
    )
    if nav_count != 1:
        raise ValueError(f"{slug}: site navigation insertion point not found")

    date_parts = [
        f'公開：<time datetime="{published}">{format_japanese_date(published)}</time>'
    ]
    if modified != published:
        date_parts.append(
            f'更新：<time datetime="{modified}">{format_japanese_date(modified)}</time>'
        )
    editor_line = (
        '<p class="editor-meta">編集：<a href="/about/">晩酌ラボ編集部</a> ｜ '
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
    document = re.sub(
        rf"\n?{re.escape(QUALITY_START)}.*?{re.escape(QUALITY_END)}\n?",
        "\n",
        document,
        flags=re.DOTALL,
    )
    compliance_start = document.find('    <aside class="compliance"')
    if compliance_start == -1:
        raise ValueError(f"{slug}: compliance insertion point not found")
    document = (
        document[:compliance_start]
        + quality_block(slug)
        + "\n\n"
        + document[compliance_start:]
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
    for position, (path, (title, _)) in enumerate(GUIDE_PAGES.items(), start=1):
        item_list.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": title,
                "url": f"{SITE_URL}{path}",
            }
        )
    for position, slug in enumerate(HOME_ORDER, start=len(GUIDE_PAGES) + 1):
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
            hints = ' decoding="async" fetchpriority="high"'
        else:
            hints = ' loading="lazy" decoding="async"'
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
        (path, lastmod)
        for path, (_, lastmod) in GUIDE_PAGES.items()
    ] + [
        (f"/p/{slug}/", modified)
        for slug in HOME_ORDER
        for _, modified in (ARTICLE_DATES[slug],)
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
    pages.extend((ROOT / "guides").glob("*/index.html"))
    for page in pages:
        document = page.read_text(encoding="utf-8")
        document = re.sub(
            r'/assets/site-info\.css\?v=[^"]+',
            f"/assets/site-info.css?v={STYLESHEET_VERSION}",
            document,
        )
        page.write_text(document, encoding="utf-8", newline="\n")


def main() -> None:
    active = set(HOME_ORDER)
    if not active <= set(ARTICLE_DATES) or not active <= set(SHORT_TITLES):
        raise ValueError("Active article metadata maps are out of sync")
    if active != set(GUIDE_RELATED) or active != set(PRE_PURCHASE_CHECKS) or active != set(EVIDENCE_LIMITS):
        raise ValueError("Content quality maps are out of sync")
    update_home()
    for slug in HOME_ORDER:
        update_article(slug)
    update_sitemap()
    update_stylesheet_version()
    print(f"Search markup applied to {len(HOME_ORDER)} comparison pages, guides, and home.")


if __name__ == "__main__":
    main()
