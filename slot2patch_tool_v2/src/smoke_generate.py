"""Exercise the frozen GUI's backend through a real create/apply/package cycle."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # An exe prefix works for the frozen build. A Python/core prefix also
    # permits checking the same fixture on macOS without a Windows runtime.
    prefix = sys.argv[1:]
    if not prefix:
        raise SystemExit("usage: smoke_generate.py BACKEND [BACKEND_ARGS...]")
    with tempfile.TemporaryDirectory(prefix="slot2patch stdio ") as folder:
        root = Path(folder)
        original = bytearray(b"\xff" * 0x40000)
        original[0xac:0xb0] = b"TSTJ"
        original[0xbc] = 0
        original[-1] = 1
        target = original.copy()
        target[0x21010:0x21020] = b"logging-smoke-ok!"
        orig, cn = root / "original test.gba", root / "target test.gba"
        orig.write_bytes(original)
        cn.write_bytes(target)
        argv = [*prefix, "--orig", str(orig), "--cn", str(cn),
                "--name", "SmokeTest", "--version", "stdio-fix 中文日志",
                "--out", str(root / "output")]
        result = subprocess.run(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, encoding="utf-8", errors="replace",
            timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        print(result.stdout)
        if result.returncode:
            raise SystemExit(f"generation failed: {result.returncode}")
        assert "==> PatchTool:" in result.stdout
        assert "    $ " in result.stdout
        assert "还原一致" in result.stdout
        assert "完成:" in result.stdout
        assert "Traceback" not in result.stdout
        applied = root / "output" / "verify_apply.gba"
        assert applied.read_bytes() == target
        packages = list((root / "output").glob("*.zip"))
        assert len(packages) == 1
        with zipfile.ZipFile(packages[0]) as package:
            assert "_gba/titles/TSTJ00.patch" in package.namelist()
            info = json.loads(package.read("PATCH_INFO.json"))
            assert info["target_sha256"] == hashlib.sha256(target).hexdigest()
            assert info["independent_exact"] and info["author_apply_exact"]
            assert not any(Path(name).suffix.lower() in (".gba", ".nds", ".sav")
                           for name in package.namelist())
        print("PASS synthetic create/apply/package with spaced paths and captured Chinese logs")


if __name__ == "__main__":
    main()
