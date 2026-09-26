"""Fetch the pinned Noto Sans JP font and its SIL Open Font License."""
from pathlib import Path
from urllib.request import urlopen
import hashlib

REVISION = "66a36c8c94b1a5d992ee4e7f392fccfe4945767c"
SOURCE = f"https://raw.githubusercontent.com/google/fonts/{REVISION}/ofl/notosansjp/"
DEST = Path(__file__).parent / "fonts"

if __name__ == "__main__":
    DEST.mkdir(parents=True, exist_ok=True)
    for remote, local in [("NotoSansJP%5Bwght%5D.ttf", "NotoSansJP.ttf"), ("OFL.txt", "OFL.txt")]:
        with urlopen(SOURCE + remote, timeout=60) as response:
            content = response.read()
        (DEST / local).write_bytes(content)
        print(local, len(content), "bytes; SHA256", hashlib.sha256(content).hexdigest())
