"""Build the A20 diagnostic candidate by patching the pinned A19 ARM7 code."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PARENT = HERE / 'GBARunner3_A19_wave.nds'
PARENT_SHA = '5936e8227f0b3f63e5bdf4c53c2254b337227f28b7f38f47a178fbf2a39ac9fe'
OUTPUT = HERE / 'GBARunner3_A20_rebuilt.nds'
CORE_LOAD = 0x03800000
CORE_FILE = 0x2D3C8


def main():
    original = PARENT.read_bytes()
    assert hashlib.sha256(original).hexdigest() == PARENT_SHA
    result = bytearray(original)
    with tempfile.TemporaryDirectory() as temp:
        obj, binary = Path(temp) / 'nr32.o', Path(temp) / 'nr32.bin'
        subprocess.run(['arm-none-eabi-as', '-o', obj, HERE / 'nr32_resume.s'], check=True)
        subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.text', obj, binary], check=True)
        resume = binary.read_bytes()
    original_resume = struct.pack(
        '<10I', 0xe3520000, 0x0affffb7, 0xe59f2178, 0xe5930000, 0xe5923000,
        0xe1530000, 0x0affffb2, 0xe5820000, 0xebfffb9e, 0xeaffffaf,
    )
    assert len(resume) == len(original_resume)
    # For the 50/25% and 100% branches, use ip for the gain pointer
    # to preserve r1 as the newly decoded selector, just as for 75%.
    changes = [(0x03805EB4, original_resume, resume)]
    for address, load in [(0x03805F68, 0xe59f112c), (0x03805FF0, 0xe59f10a4)]:
        changes.append((
            address,
            struct.pack('<2I', load, 0xe5810008),
            struct.pack('<2I', (load & ~0xf000) | 0xc000, 0xe58c0008),
        ))
    for address, before, after in changes:
        off = CORE_FILE + address - CORE_LOAD
        assert result[off:off+len(before)] == before
        result[off:off+len(before)] = after
    OUTPUT.write_bytes(result)
    print(hashlib.sha256(result).hexdigest(), OUTPUT.name)


if __name__ == '__main__':
    main()
