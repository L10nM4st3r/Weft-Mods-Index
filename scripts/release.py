"""`release.py <artifacts dir> <state dir>`, the builds in $BUILDS: each built for every system packed
into one zip the way `weft --pack-mod` does (a library per system at the top, `assets/`), put in a
release of this repository, and written down in state.json; what didn't build on every system is
written down as failed. Runs none of the mods' code: the assets come from a plain checkout.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from plan import load_state

SYSTEMS = {"windows": "{id}.dll", "linux": "lib{id}.so", "macos": "lib{id}.dylib"}


def key(b):
    return f"{b['id']}-{b['version']}-{b['target']}"


def assets(b, into):
    """The mod's assets at its commit, without running anything of it."""
    run = lambda *a: subprocess.run(["git", *a], cwd=into, check=True, capture_output=True)
    run("init", "-q")
    run("fetch", "-q", "--depth=1", b["repo"], b["commit"])
    run("checkout", "-q", "FETCH_HEAD")
    return into / b["dir"] / "assets"


def pack(b, libs, out):
    path = out / f"{b['id']}.zip"
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, lib in libs.items():
            z.write(lib, name)
        folder = assets(b, Path(tmp))
        for f in sorted(folder.rglob("*")) if folder.is_dir() else []:
            if f.is_file() and not f.is_symlink():
                z.write(f, "assets/" + f.relative_to(folder).as_posix())
    return path


def main(artifacts, state_dir):
    builds = json.loads(os.environ["BUILDS"])
    repo = os.environ["GITHUB_REPOSITORY"]
    state = load_state(state_dir)
    abis = {}
    out = Path(tempfile.mkdtemp())
    for b in builds:
        k = key(b)
        libs, missing = {}, []
        for system, file in SYSTEMS.items():
            lib = Path(artifacts) / f"lib-{k}-{system}" / file.format(id=b["id"])
            if lib.is_file():
                libs[lib.name] = lib
            else:
                missing.append(system)
        entry = {f: b[f] for f in ("id", "version", "commit", "target", "auto")}
        if missing:
            print(f"::warning::{k} didn't build for {', '.join(missing)}")
            state["failed"].append(entry)
            continue
        if b["target"] not in abis:
            url = f"https://github.com/Weft-Rust/Weft/releases/download/{b['target']}/mod-abi.txt"
            abis[b["target"]] = urllib.request.urlopen(url).read().decode().strip()
        zip_path = pack(b, libs, out)
        sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        title = f"{b['id']} {b['version']} for Weft {b['target']}"
        notes = f"Built from {b['repo']}/tree/{b['commit']}" + (f"/{b['dir']}" if b["dir"] else "")
        if b["auto"]:
            notes += f", submitted for {b['weft']} and built again for {b['target']}"
        subprocess.run(["gh", "release", "create", k, str(zip_path), "--repo", repo, "--title", title, "--notes", notes], check=True)
        state["built"].append(entry | {"abi": abis[b["target"]], "sha256": sha,
                                       "url": f"https://github.com/{repo}/releases/download/{k}/{zip_path.name}"})
        print(f"{k}: {sha}")
    (Path(state_dir) / "state.json").write_text(json.dumps(state, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
