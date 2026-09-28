"""Copy Git-owned public files into dist, excluding tools, fonts, and metadata."""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED = {"tools", "dist", "node_modules", "functions"}

# The bootstrap runs on main BEFORE this PR is merged as well as on feature branches.
# It uses only Python's standard library and tracked files; no repo script is required.
BOOTSTRAP = (
    "from pathlib import Path; import shutil,subprocess; "
    "o=Path('dist'); "
    "paths=subprocess.check_output(['git','ls-files','-z']).decode('utf-8').split(chr(0)); "
    "files=[Path(s) for s in paths if s and Path(s).parts[0] not in "
    "('tools','dist','node_modules','functions') and not any("
    "p.startswith('.') and p!='.well-known' for p in Path(s).parts)]; "
    "[( (o/p).parent.mkdir(parents=True,exist_ok=True),shutil.copy2(p,o/p)) for p in files]"
)
BUILD_COMMAND = 'python3 -c "' + BOOTSTRAP + '"'


def is_public(path: str) -> bool:
    """Define the same public file boundary for local and Cloudflare packaging."""
    parts = PurePosixPath(path).parts
    return bool(parts) and parts[0] not in EXCLUDED and not any(
        p.startswith(".") and p != ".well-known" for p in parts)


def package(include_untracked: bool = False) -> int:
    """Package a fresh dist directory; refuse to retain stale files from an old run."""
    output = ROOT / "dist"
    if output.exists() and any(p.name != ".gitignore" for p in output.iterdir()):
        raise SystemExit("dist already contains a build. Remove that generated directory before repackaging.")
    args = ["git", "ls-files", "-z"]
    if include_untracked:
        args += ["--cached", "--others", "--exclude-standard"]
    files = sorted(set(subprocess.check_output(args, cwd=ROOT).decode("utf-8").split("\0")))
    output.mkdir(exist_ok=True)
    # Ignore this directory locally without editing the repository's existing .gitignore.
    (output / ".gitignore").write_text("*\n", encoding="utf-8")
    count = 0
    for name in files:
        if not is_public(name):
            continue
        source = ROOT / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Expected regular file: {name}")
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        count += 1
    print(f"Packaged {count} public files into dist; tools and fonts excluded.")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-untracked", action="store_true", help="Include new files for local preview before git add.")
    parser.add_argument("--print-build-command", action="store_true", help="Print the main-compatible Cloudflare build command.")
    options = parser.parse_args()
    if options.print_build_command:
        print(BUILD_COMMAND)
    else:
        package(options.include_untracked)
