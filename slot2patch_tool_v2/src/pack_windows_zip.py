"""把 PyInstaller onedir 目录打成发布 zip。拒绝打进 ROM / NDS / BIOS。"""
import hashlib
import sys
import zipfile
from pathlib import Path

BAD_SUFFIX = {".gba", ".nds", ".sav", ".bios"}
BAD_NAMES = {"bios.bin", "gba_bios.bin", "nds_bios.bin", "bios.gba", "bios.nds"}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: pack_windows_zip.py DIST_DIR ZIP_PATH", file=sys.stderr)
        return 2
    dist = Path(sys.argv[1])
    zip_path = Path(sys.argv[2])
    if not dist.is_dir():
        print(f"missing dist dir: {dist}", file=sys.stderr)
        return 1
    files = [p for p in dist.rglob("*") if p.is_file()]
    if not files:
        print(f"empty dist dir: {dist}", file=sys.stderr)
        return 1
    for p in files:
        name = p.name.lower()
        if p.suffix.lower() in BAD_SUFFIX or name in BAD_NAMES:
            print(f"refusing ROM/BIOS-like file: {p}", file=sys.stderr)
            return 1
        if "__pycache__" in p.parts:
            print(f"refusing bytecode cache: {p}", file=sys.stderr)
            return 1
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(files):
            zf.write(p, p.relative_to(dist).as_posix())
    data = zip_path.read_bytes()
    print(f"sha256={hashlib.sha256(data).hexdigest()}")
    print(f"bytes={len(data)}")
    print(f"files={len(files)}")
    print(f"zip={zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
