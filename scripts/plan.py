"""What to build next: `plan.py <state dir>`, the `builds` output for one mod and `more` if others wait.

A submitted build is built against the Weft it names. The newest version of each mod is also
built again for every Weft release after that, with nothing changed but the SDK's tag; what fails
to build stays failed and isn't tried again. One mod a run: its code runs while it is built, and
must not reach another mod's files.
"""
import json
import sys
from pathlib import Path

from common import all_builds, github, output, version_key

WEFT = "Weft-Rust/Weft"


def weft_releases():
    """Weft releases mods can be built for (those that tell their mod ABI), oldest first."""
    out = []
    for r in github(f"https://api.github.com/repos/{WEFT}/releases?per_page=100"):
        if r["draft"] or not any(a["name"] == "mod-abi.txt" for a in r["assets"]):
            continue
        out.append(r["tag_name"])
    return sorted(out, key=tag_key)


def tag_key(tag):
    return tuple(int(n) for n in tag.lstrip("v").split("."))


def load_state(state_dir):
    path = Path(state_dir) / "state.json"
    return json.loads(path.read_text()) if path.exists() else {"built": [], "failed": []}


def main(state_dir):
    state = load_state(state_dir)
    done = {(b["id"], b["version"], b["target"]) for b in state["built"] + state["failed"]}
    releases = weft_releases()
    todo = []
    builds = all_builds()
    for b in builds:
        if b["weft"] in releases and (b["id"], b["version"], b["weft"]) not in done:
            todo.append(b | {"target": b["weft"], "auto": False})
    newest = {}
    for b in builds:
        if b["id"] not in newest or version_key(b["version"]) > version_key(newest[b["id"]]["version"]):
            newest[b["id"]] = b
    for b in newest.values():
        for tag in releases:
            if tag_key(tag) > tag_key(b["weft"]) and (b["id"], b["version"], tag) not in done:
                todo.append(b | {"target": tag, "auto": True})
    first = todo[0]["id"] if todo else None
    run = [{k: t[k] for k in ("id", "version", "repo", "dir", "commit", "weft", "target", "auto")}
           for t in todo if t["id"] == first]
    print(f"{len(run)} builds of {first}, {len(todo) - len(run)} after" if run else "nothing to build")
    output("builds", json.dumps(run))
    output("more", "true" if len(todo) > len(run) else "false")


if __name__ == "__main__":
    main(sys.argv[1])
