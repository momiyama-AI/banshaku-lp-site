"""Regression checks for published comparison sales paths (no external clicks)."""
from html import unescape
from pathlib import Path
import re
import unittest

from upgrade_purchase_path import upgrade, CARD, STACK, LINK

ROOT = Path(__file__).resolve().parents[1]


class PurchasePathTests(unittest.TestCase):
    def test_all_published_comparisons_preserve_destinations(self):
        sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
        slugs = re.findall(r'https://banshaku-lp-site.pages.dev/p/([^/]+)/', sitemap)
        self.assertEqual(len(slugs), 14)
        for slug in slugs:
            with self.subTest(slug=slug):
                html = (ROOT / 'p' / slug / 'index.html').read_text(encoding='utf-8')
                self.assertEqual(upgrade(html), html, 'Upgrade must be idempotent')
                cards, stacks = CARD.findall(html), STACK.findall(html)
                self.assertEqual(len(cards), len(stacks))
                self.assertGreaterEqual(len(cards), 3)
                for card, stack in zip(cards, stacks):
                    original = {(store, unescape(url)) for store, url in LINK.findall(stack)}
                    top = {(store, unescape(url)) for store, url in re.findall(r'class="verdict-shop-link verdict-shop-(rakuten|amazon)" href="([^\"]+)"', card)}
                    self.assertEqual(top, original)
                    self.assertIn('href="#comparison-heading"', card)
                    self.assertIn('class="verdict-product-image"', card)
                    if original:
                        self.assertNotIn('比較対象（リンクなし）', stack)
                        self.assertIn('rel="nofollow sponsored noopener"', card)
                self.assertIn('Reader value:start', html)


if __name__ == '__main__':
    unittest.main()
