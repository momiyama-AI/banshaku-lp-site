"""Exercise the main-compatible build with tracked public and private fixtures."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from package_site import BOOTSTRAP, is_public


class PackagingTest(unittest.TestCase):
    def test_old_main_without_new_scripts_and_file_preservation(self):
        with tempfile.TemporaryDirectory(prefix="shindan-package-") as directory:
            root = Path(directory)
            files = {
                "index.html": b"existing top",
                "_redirects": b"/old/ / 301\n",
                "assets/social/photo.png": b"unchanged bytes",
                ".well-known/example": b"public well known",
                "tools/legacy.py": b"private tool",
                "tools/shindan/fonts/font.ttf": b"private font",
                ".gitignore": b"__pycache__/\n",
            }
            for name, content in files.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            # Deliberately no tools/shindan/package_site.py exists in this old-main fixture.
            subprocess.run([sys.executable, "-c", BOOTSTRAP], cwd=root, check=True)
            actual = {p.relative_to(root / "dist").as_posix(): p.read_bytes()
                      for p in (root / "dist").rglob("*") if p.is_file()}
            self.assertEqual(actual, {n: c for n, c in files.items() if is_public(n)})
            self.assertFalse((root / "dist/tools").exists())
            self.assertFalse((root / "dist/.git").exists())
            self.assertEqual((root / "index.html").read_bytes(), files["index.html"])


if __name__ == "__main__":
    unittest.main()
