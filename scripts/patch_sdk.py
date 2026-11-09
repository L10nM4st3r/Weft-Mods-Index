"""`patch_sdk.py <mod dir> <weft checkout>`: builds the mod against the Weft of that checkout (the
game's repository at the tag being built for). Every weft_sdk and base_api in the build, the
mod's own and those of its path dependencies and libraries alike, whether pinned by tag or by
branch, come from the checkout: a `[patch]` for the whole dependency graph, written to the mod's
`.cargo/config.toml`, so no manifest is edited."""
import sys
from pathlib import Path

SOURCE = "https://github.com/Weft-Rust/Weft"
# The game's crates a mod may depend on, by where they are in its repository.
CRATES = {"weft_sdk": "crates/sdk", "base_api": "mods/base/api"}

mod, weft = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
lines = [f'[patch."{SOURCE}"]']
for name, rel in CRATES.items():
    path = weft / rel
    if not (path / "Cargo.toml").is_file():
        sys.exit(f"{path}: no {name} in the Weft checkout")
    lines.append(f"{name} = {{ path = '{path.as_posix()}' }}")
config = mod / ".cargo" / "config.toml"
config.parent.mkdir(parents=True, exist_ok=True)
old = config.read_text(encoding="utf-8") if config.is_file() else ""
if f'[patch."{SOURCE}"]' in old:
    sys.exit(f"{config}: has a patch of {SOURCE} already")
config.write_text(old + ("\n" if old and not old.endswith("\n") else "") + "\n".join(lines) + "\n", encoding="utf-8")
print(f"weft_sdk and base_api from {weft}")
