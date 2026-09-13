"""Add mobile-readable sales paths without overwriting curated article content.

The shared pipeline template also contains this layout for newly generated pages.
Existing affiliate destinations, source dates and reader-value sections are preserved.
Run from any directory; a second run is a no-op.
"""
from html import escape, unescape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CARD = re.compile(r'<article class="verdict-item[^\"]*">.*?</article>', re.S)
STACK = re.compile(r'<div class="cta-stack">(.*?)</div>', re.S)
HEADER = re.compile(r'<th class="prod"[^>]*>(.*?)</th>', re.S)
LINK = re.compile(r'<a class="(rakuten|amazon)-button" href="([^\"]+)"[^>]*>.*?</a>', re.S)


def upgrade(source: str) -> str:
    if 'class="verdict-actions"' in source or 'class="verdict-item' not in source:
        return source
    cards, stacks, headers = CARD.findall(source), STACK.findall(source), HEADER.findall(source)
    if not (len(cards) == len(stacks) == len(headers)):
        raise ValueError("Product cards, headers and sales destinations must align")
    for card, stack, header in zip(cards, stacks, headers):
        name = re.search(r'<div class="name">(.*?)</div>', header, re.S)
        photo = re.search(r'<img\b[^>]+>', header)
        if not name or not photo:
            raise ValueError("Product name or image missing")
        full_name = unescape(re.sub(r'<[^>]+>', ' ', name[1])).strip()
        image = photo[0].replace('<img ', '<img class="verdict-product-image" width="96" height="96" ', 1)
        model = re.search(r'<small>(.*?)</small>', name[1], re.S)
        intro = f'\n        <span class="verdict-model">{model[1] if model else escape(full_name)}</span>\n        {image}'
        upgraded = card.replace('</strong>', '</strong>' + intro, 1)
        actions = []
        for store, destination in LINK.findall(stack):
            label = '楽天市場で価格・在庫を確認 →' if store == 'rakuten' else 'Amazonで商品を確認 →'
            actions.append(f'<a class="verdict-shop-link verdict-shop-{store}" href="{destination}" target="_blank" rel="nofollow sponsored noopener" aria-label="{escape(full_name, quote=True)}：{label}（広告）" data-placement="verdict" data-store="{store}">{label}</a>')
        actions.append('<a class="verdict-detail-link" href="#comparison-heading">仕様・注意点を詳しく比較 ↓</a>')
        if actions[:-1]:
            actions.append('<p class="verdict-price-note">広告リンクです。現在の価格・送料・在庫は販売先でご確認ください。</p>')
        upgraded = upgraded.replace('</article>', '<div class="verdict-actions">' + '\n'.join(actions) + '</div>\n      </article>')
        source = source.replace(card, upgraded, 1)
    def correct_empty_label(match: re.Match) -> str:
        stack = match[0]
        if LINK.search(stack):
            stack = stack.replace('<span class="comparison-only">比較対象（リンクなし）</span>', '')
        return stack
    return STACK.sub(correct_empty_label, source)


if __name__ == '__main__':
    changed = 0
    # Only published comparisons; retired URLs are intentionally excluded.
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    for slug in re.findall(r'https://banshaku-lp-site.pages.dev/p/([^/]+)/', sitemap):
        path = ROOT / 'p' / slug / 'index.html'
        source = path.read_text(encoding='utf-8')
        result = upgrade(source)
        if result != source:
            path.write_text(result, encoding='utf-8')
            changed += 1
    print(f'Updated {changed} published comparisons')
