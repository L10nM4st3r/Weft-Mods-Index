"""`patch_sdk.py <Cargo.toml> <tag>`: the mod's weft_sdk from the game's repository at another tag,
for a build of the same code for a newer Weft."""
import re
import sys
from pathlib import Path

SDK = re.compile(r'^(\s*weft_sdk\s*=\s*\{[^}]*git\s*=\s*"https://github\.com/Weft-Rust/Weft"[^}]*tag\s*=\s*")[^"]*(")', re.M)

path, tag = Path(sys.argv[1]), sys.argv[2]
text, n = SDK.subn(lambda m: m.group(1) + tag + m.group(2), path.read_text(encoding="utf-8"))
if n != 1:
    sys.exit(f"{path}: no weft_sdk = {{ git = \"https://github.com/Weft-Rust/Weft\", tag = \"...\" }} line")
path.write_text(text, encoding="utf-8")
print(f"weft_sdk at {tag}")
