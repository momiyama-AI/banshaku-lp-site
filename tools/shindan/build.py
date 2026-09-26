"""Generate 18 static diagnosis pages and 17 share images from the JSON data."""
from __future__ import annotations

import argparse
import html
import itertools
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse

from PIL import Image, ImageDraw, ImageFont

BASE_URL = "https://banshaku-lp-site.pages.dev"
ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "shindan"
FONT = Path(__file__).parent / "fonts" / "NotoSansJP.ttf"
TITLE = "晩酌つまみ16タイプ診断"
FOOTER = "お酒は20歳になってから。飲酒運転は法律で禁止されています。"


def read_data() -> tuple[dict, list, list]:
    """Load and validate authoring inputs before writing any generated file."""
    data = json.loads((SITE / "data/types.json").read_text(encoding="utf-8"))
    questions = json.loads((SITE / "data/questions.json").read_text(encoding="utf-8"))
    recipes = json.loads((SITE / "data/recipes.json").read_text(encoding="utf-8"))
    codes = {"".join(parts) for parts in itertools.product("SK", "CG", "RT", "OA")}
    assert len(data["types"]) == 16 and {t["code"] for t in data["types"]} == codes
    assert [a["letters"] for a in data["axes"]] == [list(p) for p in ("SK", "CG", "RT", "OA")]
    assert [a["weight"] for a in data["axes"]] == [8, 4, 2, 1]
    assert [g["code"] for g in data["groups"]] == ["SC", "SG", "KC", "KG"]
    assert len(questions) == 12 and [q["id"] for q in questions] == list(range(1, 13))
    for axis in data["axes"]:
        matching = [q for q in questions if q["axis"] == axis["id"]]
        assert len(matching) == 3
        assert all(len(q["choices"]) == 2 and
                   {c["letter"] for c in q["choices"]} == set(axis["letters"]) for q in matching)
    assert len(recipes) >= 3
    assert len({r["name"] for r in recipes}) == len(recipes), "Recipe names must be unique"
    for recipe in recipes:
        assert recipe["tags"] in codes and recipe["name"].strip()
        if recipe["url"]:
            url = urlparse(recipe["url"])
            assert url.scheme == "https" and url.netloc and not url.username
    return data, questions, recipes


def esc(value: str) -> str:
    """Escape text and attribute values."""
    return html.escape(value, quote=True)


def absolute(path: str) -> str:
    """Use one base URL for every canonical and social URL."""
    return BASE_URL.rstrip("/") + path


def page(title: str, description: str, path: str, image: str, content: str,
         script: str = "", attrs: str = "", main_class: str = "") -> str:
    """Render the shared accessible shell, metadata, navigation, and footer."""
    url = absolute(path)
    og = absolute("/shindan/og/" + image + ".png")
    module = f'<script type="module" src="/shindan/assets/{script}.js"></script>' if script else ""
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="晩酌ラボ">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{og}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{esc(title)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{og}">
  <link rel="stylesheet" href="/shindan/assets/style.css">
  {module}
</head>
<body {attrs}>
  <a class="skip" href="#main">本文へスキップ</a>
  <header class="site-header"><div class="header-inner">
    <a class="brand" href="/">晩酌ラボ</a>
    <a class="header-link" href="/shindan/types/">全16タイプ</a>
  </div></header>
  <main id="main" class="{main_class}" tabindex="-1">{content}</main>
  <footer><p>{FOOTER}</p>
    <p>運営：晩酌ラボ（<a href="https://x.com/banshaku_lab" target="_blank" rel="noopener noreferrer">@banshaku_lab</a>）</p>
    <a href="/">晩酌ラボのトップへ</a>
  </footer>
</body>
</html>
"""


def group_style(group: dict) -> str:
    """Expose both accessible light and dark group colors."""
    return f'--group-color:{group["color"]};--group-dark:{group["darkColor"]}'


def top_page(data: dict) -> str:
    """Render the entry page, quiz container, and no-JavaScript guidance."""
    groups = "".join(
        f'<div class="mini-group" style="{group_style(g)}"><span aria-hidden="true">{g["emoji"]}</span>'
        f'<strong>{g["name"]}</strong></div>' for g in data["groups"])
    content = f"""
    <section id="intro">
      <div class="intro-hero">
        <p class="eyebrow">BANSHAKU LAB / FIND YOUR TASTE</p>
        <h1>晩酌つまみ<br><span class="hero-number">16</span>タイプ診断</h1>
        <p class="lead">唐揚げにレモン、かける？<br>いつもの選び方に、あなたらしさがある。</p>
        <div class="facts"><span class="time-tag">12問・約1分</span></div>
        <p class="age-note">20歳以上の方を対象としています</p>
        <button id="start" class="button full" type="button" disabled>読み込み中…</button>
        <p class="small-note">直感で2択に答えるだけ。登録は不要です。</p>
        <div id="load-error" class="error" role="alert" hidden>設問を読み込めませんでした。通信状態を確認してお試しください。</div>
        <button id="retry" class="button secondary full" type="button" hidden>もう一度読み込む</button>
        <noscript><p class="error">診断にはJavaScriptを有効にしてください。<a href="/shindan/types/">全16タイプの一覧</a>はそのままご覧いただけます。</p></noscript>
      </div>
      <div class="group-preview" aria-label="4つのグループ">{groups}</div>
      <div class="intro-tail"><a href="/shindan/types/">あなたはどのタイプ？ 全16タイプを見る →</a>
        <p class="small-note">つまみの好みを楽しむ診断です。回答は保存・送信しません。</p></div>
    </section>
    <section id="quiz" class="quiz-card" aria-labelledby="question" hidden>
      <div class="quiz-meta"><span id="counter">Q1 / 12</span><span class="quiz-hint">直感で選んでください</span></div>
      <progress id="progress" max="12" value="1" aria-label="全12問中1問目"></progress>
      <h1 id="question" tabindex="-1"></h1>
      <div id="choices" role="group" aria-labelledby="question"></div>
      <button id="back" class="back-button" type="button" disabled>← 前の質問へ</button>
    </section>
    <section id="pending" class="pending" hidden aria-live="polite">
      <div class="pending-dot" aria-hidden="true"></div>
      <h1 id="pending-title" tabindex="-1">判定中…</h1>
      <p class="lead">今夜の好みを、ひとつのタイプに。</p>
    </section>"""
    return page(TITLE + "｜晩酌ラボ",
                "12問・約1分。2択でわかる、あなたの晩酌つまみタイプ。全16タイプから好みと今夜のおすすめつまみを見つけよう。20歳以上の方が対象です。",
                "/shindan/", "top", content, "quiz")


def recommend(code: str, recipes: list, axes: list) -> list:
    """Mirror the public scoring rule for useful static fallbacks."""
    ranked = sorted(enumerate(recipes), key=lambda pair: (
        -sum(a["weight"] for i, a in enumerate(axes) if pair[1]["tags"][i] == code[i]), pair[0]))
    return [recipe for _, recipe in ranked[:3]]


def recipe_items(recipes: list) -> str:
    """Render recipe names and only nonempty HTTPS recipe links."""
    items = []
    for recipe in recipes:
        link = (f'<a href="{esc(recipe["url"])}" target="_blank" rel="noopener noreferrer" '
                f'aria-label="{esc(recipe["name"])}のレシピを見る（新しいタブ）">レシピを見る</a>') if recipe["url"] else ""
        items.append(f'<li><span>{esc(recipe["name"])}</span>{link}</li>')
    return "".join(items)


def result_page(item: dict, data: dict, recipes: list) -> str:
    """Embed identity, drinks, compatibility, and social links in static HTML."""
    code, name, line = item["code"], item["name"], item["line"]
    group = next(g for g in data["groups"] if code.startswith(g["code"]))
    opposite = "".join(next(x for x in a["letters"] if x != code[i])
                       for i, a in enumerate(data["axes"]))
    partner = next(t for t in data["types"] if t["code"] == opposite)
    bars = ""
    for axis in data["axes"]:
        left, right = axis["labels"]
        bars += f"""<div class="axis">
          <div class="axis-heading"><span>{axis["name"]}</span><span class="axis-picked"></span></div>
          <div class="axis-labels"><span class="axis-label">{left}</span><span class="axis-label">{right}</span></div>
          <div class="axis-track" role="meter" aria-label="{axis["name"]}：{left}の割合" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"></div>
        </div>"""
    path = f"/shindan/result/{code.lower()}/"
    url = absolute(path)
    share_text = f"私は【{name}】（{code}）でした！あなたの晩酌つまみタイプは？"
    x = "https://x.com/intent/tweet?" + urlencode({
        "text": share_text, "url": url, "hashtags": "つまみ診断,晩酌ラボ", "via": "banshaku_lab"})
    threads = "https://www.threads.net/intent/post?" + urlencode({"text": share_text + "\n#つまみ診断\n" + url})
    content = f"""
    <article class="result-hero" aria-labelledby="type-name">
      <div class="result-topline"><p id="result-label">こんなつまみタイプも</p>
        <span class="group-badge"><span aria-hidden="true">{group["emoji"]}</span>{group["name"]}</span></div>
      <p class="result-code">{code}</p>
      <h1 id="type-name" class="result-name">{esc(name)}</h1>
      <p class="result-line">{esc(line)}</p>
      <dl class="drinks"><dt>合うお酒</dt><dd>{group["drinks"]}</dd></dl>
    </article>
    <div class="result-cta"><a id="diagnose-cta" class="button full" href="/shindan/">あなたも診断する</a></div>
    <section id="personal-result" class="section" aria-labelledby="personal-title" hidden>
      <p class="eyebrow">YOUR TASTE</p><h2 id="personal-title">あなたの結果</h2>{bars}
      <p class="small-note">各軸3問の回答から算出した、好みの割合です。</p>
    </section>
    <section class="section" aria-labelledby="recipes-title">
      <p class="eyebrow">TONIGHT'S MENU</p><h2 id="recipes-title">今夜のおすすめつまみ</h2>
      <ol id="recipes" class="recipe-list">{recipe_items(recommend(code, recipes, data["axes"]))}</ol>
      <p id="recipe-note" class="small-note" hidden>最新のレシピ情報を取得できなかったため、ページ作成時のおすすめを表示しています。</p>
    </section>
    <section class="section" aria-label="相性のよいタイプ"><div class="compatibility">
      <p class="eyebrow">相性◎の飲み仲間</p>
      <p class="compat-code">{opposite}</p>
      <h2><a href="/shindan/result/{opposite.lower()}/">{esc(partner["name"])}</a></h2>
      <p>頼むものが一切かぶらないので、取り合いにならない最高の飲み仲間</p>
    </div></section>
    <section class="section" aria-labelledby="share-title">
      <h2 id="share-title">あなたのタイプをシェア</h2>
      <div class="share-grid">
        <a id="share-x" class="button" href="{esc(x)}" target="_blank" rel="noopener noreferrer">Xでシェア</a>
        <a id="share-threads" class="button secondary" href="{esc(threads)}" target="_blank" rel="noopener noreferrer">Threadsでシェア</a>
        <button id="copy-link" class="button secondary" type="button">リンクをコピー</button>
        <button id="share-more" class="button secondary" type="button" hidden>その他</button>
      </div>
      <p id="share-status" role="status"></p>
      <label id="copy-fallback" hidden>共有するURL<input type="text" readonly aria-label="共有するURL"></label>
    </section>
    <aside class="follow-box">
      <p><strong>今夜の「あと一品」を、晩酌ラボで。</strong><br>つまみのアイデアをお届けしています。</p>
      <a class="button full" href="https://x.com/banshaku_lab" target="_blank" rel="noopener noreferrer">@banshaku_lab をフォロー</a>
      <a id="threads-profile" class="button full" hidden target="_blank" rel="noopener noreferrer">Threadsでもフォロー</a>
    </aside>
    <nav class="end-links" aria-label="診断メニュー">
      <a href="/shindan/">もう一度診断する</a><a href="/shindan/types/">全16タイプを見る</a>
    </nav>"""
    return page(f"{name}（{code}）｜{TITLE}｜晩酌ラボ", f"{line} {group['name']}の{name}。合うお酒は{group['drinks']}。12問であなたのタイプも診断。",
                path, code.lower(), content, "result",
                f'data-code="{code}" data-group="{group["code"]}"', "result-main")


def types_page(data: dict) -> str:
    """Render all 16 links, grouped in the source-data order."""
    groups = []
    for group in data["groups"]:
        cards = "".join(
            f'<a class="type-link" href="/shindan/result/{t["code"].lower()}/">'
            f'<span class="compat-code">{t["code"]}</span><strong>{esc(t["name"])}</strong>'
            f'<p>{esc(t["line"])}</p></a>' for t in data["types"] if t["code"].startswith(group["code"]))
        groups.append(f'<section class="type-group" style="{group_style(group)}">'
                      f'<h2>{group["emoji"]} {group["name"]}</h2>'
                      f'<p class="small-note">合うお酒：{group["drinks"]}</p>'
                      f'<div class="type-grid">{cards}</div></section>')
    content = f"""<p class="eyebrow">FIND YOUR DRINKING COMPANY</p>
    <h1 class="types-heading">晩酌つまみ<br>全16タイプ</h1>
    <p class="lead">小鉢をちびちび。大皿をがっつり。<br>どの晩酌にも、その人らしい「好き」がある。</p>
    <a class="button full" href="/shindan/">12問で、あなたのタイプを診断</a>
    {"".join(groups)}
    <div class="section"><a class="button full" href="/shindan/">あなたも診断する</a></div>"""
    return page("全16タイプ一覧｜" + TITLE + "｜晩酌ラボ",
                "小鉢派・ヘルシー派・バー派・酒場派。晩酌つまみ16タイプの名前、特徴、合うお酒を一覧で紹介します。",
                "/shindan/types/", "top", content)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Use the bundled Noto Sans JP variable font for consistent Japanese PNGs."""
    result = ImageFont.truetype(str(FONT), size)
    result.set_variation_by_axes([700 if bold else 400])
    return result


def wrap_text(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont,
              width: int) -> list[str]:
    """Wrap Japanese text by measured glyph width without clipping."""
    lines, current = [], ""
    for char in text:
        if current and draw.textlength(current + char, font=face) > width:
            lines.append(current)
            current = char
        else:
            current += char
    if current:
        lines.append(current)
    return lines


def og_image(item: dict | None, group: dict | None, groups: list) -> Image.Image:
    """Draw a 1200×630 share card using local type and restrained group color."""
    canvas = Image.new("RGB", (1200, 630), "#f7f3ec")
    draw = ImageDraw.Draw(canvas)
    color = group["color"] if group else "#966016"
    draw.rectangle((0, 0, 1200, 18), fill=color)
    draw.rounded_rectangle((48, 46, 1152, 566), radius=22, fill="#fffdfa", outline="#d9d1c5", width=2)
    # Plate and chopsticks stay behind the code, clear of all name and copy lines.
    draw.ellipse((932, 88, 1095, 251), outline="#e9e2d7", width=3)
    draw.ellipse((953, 109, 1074, 230), outline="#e9e2d7", width=2)
    draw.line((1050, 72, 1100, 246), fill=color, width=7)
    draw.line((1074, 69, 1124, 243), fill=color, width=7)
    if item:
        draw.text((78, 71), group["name"], font=font(29, True), fill=color)
        draw.text((76, 132), item["code"], font=font(94, True), fill=color)
        name_font = font(61, True)
        while draw.textlength(item["name"], font=name_font) > 1040:
            name_font = font(name_font.size - 1, True)
        draw.text((78, 272), item["name"], font=name_font, fill="#162033")
        draw.line((78, 387, 1122, 387), fill="#d9d1c5", width=2)
        copy_font = font(29)
        lines = wrap_text(draw, item["line"], copy_font, 1040)
        assert len(lines) <= 3, "OGP description needs editorial shortening"
        for i, line in enumerate(lines):
            draw.text((78, 414 + 43 * i), line, font=copy_font, fill="#39485b")
    else:
        draw.text((78, 76), "12問・約1分", font=font(29, True), fill=color)
        draw.text((74, 165), "晩酌つまみ", font=font(63, True), fill="#162033")
        draw.text((71, 247), "16タイプ診断", font=font(89, True), fill="#162033")
        draw.text((78, 382), "いつもの選び方に、あなたらしさがある。", font=font(29), fill="#39485b")
        for i, g in enumerate(groups):
            x = 80 + 258 * i
            draw.ellipse((x, 488, x + 16, 504), fill=g["color"])
            draw.text((x + 28, 473), g["name"], font=font(25, True), fill=g["color"])
    draw.text((58, 583), TITLE + "｜晩酌ラボ", font=font(22, True), fill="#39485b")
    return canvas


def generate(skip_images: bool = False) -> None:
    """Regenerate only files owned by this feature."""
    data, _, recipes = read_data()
    if not skip_images and not FONT.is_file():
        raise SystemExit("Noto Sans JP is missing. Run: python tools/shindan/download_font.py")
    # Validate the font before writing HTML.
    if not skip_images:
        font(22)
    pages = {SITE / "index.html": top_page(data), SITE / "types/index.html": types_page(data)}
    for item in data["types"]:
        pages[SITE / "result" / item["code"].lower() / "index.html"] = result_page(item, data, recipes)
    for path, markup in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markup, encoding="utf-8", newline="\n")
    if not skip_images:
        (SITE / "og").mkdir(exist_ok=True)
        og_image(None, None, data["groups"]).save(SITE / "og/top.png", optimize=True)
        for item in data["types"]:
            group = next(g for g in data["groups"] if item["code"].startswith(g["code"]))
            og_image(item, group, data["groups"]).save(SITE / "og" / (item["code"].lower() + ".png"), optimize=True)
    print(f"Generated {len(pages)} HTML pages" + ("" if skip_images else " and 17 PNGs (1200x630)."))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-images", action="store_true", help="HTML-only work when the font is unavailable; not a complete build.")
    generate(parser.parse_args().skip_images)
