"""What every script reads: the submitted builds under mods/, their rules, the maintainers."""
import json
import os
import re
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ID = re.compile(r"^[a-z0-9_]{1,64}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
TAG = re.compile(r"^v\d+\.\d+\.\d+$")
REPO = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FIELDS = {"name": str, "summary": str, "author": str, "repo": str, "dir": str, "commit": str,
          "weft": str, "deps": list, "owner": str, "reviewed": str}
# Ships with the game.
RESERVED = {"base", "core"}


def maintainers(root=ROOT):
    path = Path(root) / "MAINTAINERS"
    return {l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")}


def read_build(root, path):
    """One submitted build, `mods/<id>/<version>.toml` under `root`, and what is wrong with it."""
    problems = []
    parts = path.parts[-3:]
    if len(parts) != 3 or parts[0] != "mods" or not parts[2].endswith(".toml"):
        return None, [f"{path}: only mods/<id>/<version>.toml files belong here"]
    mod_id, version = parts[1], parts[2][:-5]
    if not ID.match(mod_id) or mod_id in RESERVED:
        problems.append(f"{path}: the id must be [a-z0-9_] and not {', '.join(sorted(RESERVED))}")
    if not VERSION.match(version):
        problems.append(f"{path}: the file name is the mod's version, like 0.2.1")
    try:
        data = tomllib.loads((root / path).read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as e:
        return None, problems + [f"{path}: {e}"]
    for key, kind in FIELDS.items():
        if not isinstance(data.get(key), kind):
            problems.append(f"{path}: `{key}` must be a {kind.__name__}")
    extra = set(data) - set(FIELDS)
    if extra:
        problems.append(f"{path}: unknown fields {sorted(extra)}")
    if problems:
        return None, problems
    if not REPO.match(data["repo"]):
        problems.append(f"{path}: `repo` is a public GitHub repository, https://github.com/<owner>/<name>")
    if not COMMIT.match(data["commit"]):
        problems.append(f"{path}: `commit` is a full commit id")
    if not TAG.match(data["weft"]):
        problems.append(f"{path}: `weft` is a Weft release tag, like v26.11.3")
    if ".." in data["dir"] or data["dir"].startswith("/"):
        problems.append(f"{path}: `dir` is a folder inside the repository")
    if not all(isinstance(d, str) and ID.match(d) for d in data["deps"]):
        problems.append(f"{path}: `deps` are mod ids")
    data.update(id=mod_id, version=version, path=str(path))
    return data, problems


def all_builds(root=ROOT):
    root, out = Path(root), []
    for path in sorted((root / "mods").glob("*/*.toml")):
        data, problems = read_build(root, path.relative_to(root))
        if data and not problems:
            out.append(data)
    return out


def version_key(v):
    nums = re.match(r"(\d+)\.(\d+)\.(\d+)", v)
    return tuple(int(n) for n in nums.groups()) + (0 if "-" in v else 1,)


def github(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def output(name, value):
    """A step output for the workflow."""
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
        f.write(f"{name}={value}\n")
