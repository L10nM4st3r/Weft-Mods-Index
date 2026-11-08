"""`index.py <state dir>`: index.json for the launcher, from the submitted builds and what was built.

A build is verified while its version's file says who reviewed it, also when it was built again
for a newer Weft: the same code. A build whose file is gone is gone from the index.
"""
import json
import sys
from pathlib import Path

from common import all_builds, version_key
from plan import load_state, tag_key


def main(state_dir):
    files = {(b["id"], b["version"]): b for b in all_builds()}
    mods = {}
    for built in load_state(state_dir)["built"]:
        f = files.get((built["id"], built["version"]))
        if not f or built["commit"] != f["commit"]:
            continue
        m = mods.setdefault(f["id"], {"id": f["id"], "builds": []})
        newest = max((b for b in files.values() if b["id"] == f["id"]), key=lambda b: version_key(b["version"]))
        m.update(name=newest["name"], summary=newest["summary"], author=newest["author"], source=newest["repo"])
        m["builds"].append({"version": f["version"], "weft": built["target"], "abi": built["abi"], "url": built["url"],
                            "sha256": built["sha256"], "deps": f["deps"], "verified": bool(f["reviewed"]),
                            "auto": built["auto"]})
    for m in mods.values():
        # Newest first, the launcher takes the first that fits.
        m["builds"].sort(key=lambda b: (version_key(b["version"]), tag_key(b["weft"])), reverse=True)
    index = {"mods": sorted(mods.values(), key=lambda m: m["name"].lower())}
    (Path(state_dir) / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(index['mods'])} mods, {sum(len(m['builds']) for m in index['mods'])} builds")


if __name__ == "__main__":
    main(sys.argv[1])
