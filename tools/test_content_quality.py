"""Regression checks for editorial fixes; these do not certify AdSense approval."""
from pathlib import Path
import re
import unittest

from validate_static_site import public_pages

ROOT = Path(__file__).resolve().parents[1]


class ContentQualityTests(unittest.TestCase):
    def test_published_comparisons_do_not_imply_test_scores(self):
        comparisons = [p for p in public_pages() if p.parent.name.endswith('-comparison-2026')]
        self.assertEqual(len(comparisons), 14)
        for page in comparisons:
            with self.subTest(page=page.parent.name):
                html = page.read_text(encoding='utf-8')
                self.assertNotIn('総合推奨', html)
                self.assertNotRegex(html, r'<span class="cell-text[^\"]*">[◎○△]')
                self.assertNotIn('class="verdict-item recommended"', html)
                self.assertNotIn('<col class="recommended">', html)
                self.assertNotRegex(html, r'価格差(?:は)?(?:約)?[\d,.]+(?:円|倍)。')

    def test_evidence_register_covers_every_comparison(self):
        expected = {p.parent.name for p in public_pages() if p.parent.name.endswith('-comparison-2026')}
        register = (ROOT / 'guides/reading-comparisons/index.html').read_text(encoding='utf-8')
        listed = set(re.findall(r'<th scope="row"><a href="/p/([^/]+)/', register))
        self.assertEqual(listed, expected)
        self.assertIn('ページの改稿日とは異なります', register)

    def test_hot_sandwich_times_are_not_cross_brand_speed_rankings(self):
        html = (ROOT / 'p/hot-sandwich-maker-comparison-2026/index.html').read_text(encoding='utf-8')
        timing_row = re.search(r'<th scope="row">焼き時間目安</th>(.*?)</tr>', html, re.S)[1]
        self.assertNotRegex(timing_row, r'(?:recolte|Toffy|Vitantonio)より|[0-9０-９]+分半(?:長い|短い)|3機種で最短')
        self.assertIn('条件をそろえた他機種との所要時間比較ではない', timing_row)
        self.assertNotIn('短時間加熱との引き換え', html)
        self.assertIn('冷めてからプレートを拭く手入れを前提に選ぶ', html)

    def test_key_guides_retain_specific_decision_limits(self):
        expected = {
            'compact-air-fryer-comparison-2026': ('生産終了', '保証', '部品', '買い足さなくてよい'),
            'hot-sandwich-maker-comparison-2026': ('パン・具材・片付け', '固定プレート', '何回焼くか', '手持ちの道具'),
            'bottle-cooler-comparison-2026': ('同じ瓶でも', '冷凍庫', 'フィットガイド', '買わない選択'),
        }
        blocks = []
        for slug, phrases in expected.items():
            html = (ROOT / 'p' / slug / 'index.html').read_text(encoding='utf-8')
            block = re.search(r'<!-- Reader value:start -->(.*?)<!-- Reader value:end -->', html, re.S)[1]
            for phrase in phrases:
                self.assertIn(phrase, block)
            blocks.append(block)
        self.assertEqual(len(set(blocks)), 3)


if __name__ == '__main__':
    unittest.main()
