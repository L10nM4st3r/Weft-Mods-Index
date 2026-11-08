"""Checks a pull request: `check.py <base checkout> <pull request checkout> <author login>`.

This script, MAINTAINERS and the builds before come from the base checkout, never from the pull
request, which could change any of them. Anyone may add a build of a mod id nobody has, or of
one that is theirs. A file once added is changed or removed only by a maintainer, and so is
`reviewed`: a build can't be swapped for another after the fact, nor verify itself. The builds
to try go to the `builds` output.
"""
import json
import subprocess
import sys
from pathlib import Path

from common import all_builds, maintainers, output, read_build


def main(base, pr, author):
    base, pr = Path(base), Path(pr)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=base, capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "fetch", "--quiet", str(base.resolve()), head], cwd=pr, check=True)
    changes = subprocess.run(["git", "diff", "--name-status", "--no-renames", f"{head}...HEAD"], cwd=pr,
                             capture_output=True, text=True, check=True).stdout.splitlines()
    staff = author in maintainers(base)
    before = {(b["id"], b["version"]): b for b in all_builds(base)}
    problems, todo = [], []
    for line in changes:
        status, path = line.split("\t", 1)
        if not path.startswith("mods/"):
            if not staff:
                problems.append(f"{path}: only maintainers change anything outside mods/")
            continue
        if status != "A" and not staff:
            problems.append(f"{path}: a build once added stays as it is; send a new version instead")
            continue
        if status == "D":
            continue
        build, bad = read_build(pr, Path(path))
        problems += bad
        if not build:
            continue
        theirs = [b for k, b in before.items() if k[0] == build["id"]]
        owner = theirs[0]["owner"] if theirs else build["owner"]
        if not staff:
            if author != owner or build["owner"] != owner:
                problems.append(f"{path}: the id {build['id']} belongs to {owner}")
            if build["reviewed"]:
                problems.append(f"{path}: `reviewed` is for the maintainer who read the source")
        taken = {b["name"].lower(): b["id"] for b in before.values() if b["id"] != build["id"]}
        if build["name"].lower() in taken:
            problems.append(f"{path}: the name {build['name']} is {taken[build['name'].lower()]}'s")
        if status == "A":
            todo.append({k: build[k] for k in ("id", "version", "repo", "dir", "commit", "weft")} | {"target": build["weft"]})
    for p in problems:
        print(f"::error::{p}")
    if not todo and not problems:
        print("nothing to build")
    output("builds", json.dumps(todo))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
