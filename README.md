# Weft mod index

The mods the Weft launcher lists. Each build is built here, from the source, by this repository's
CI, and the launcher checks every file it downloads against the SHA-256 written down then.

- **Verified**: a maintainer read the source of that commit. The launcher shows these.
- **Not verified**: anything else that builds. The launcher shows these only when asked to, with a
  warning.

Only mods with public source get in: there's nothing to build or review otherwise.

## Sending a mod

Your mod's `Cargo.toml` takes the SDK from the game's repository at a release tag:

```toml
weft_sdk = { git = "https://github.com/Weft-Rust/Weft", tag = "v26.11.3" }
```

Commit and push, then from the game's folder:

```
weft --submit-mod path/to/your/mod
```

It builds the mod once to be sure, then opens a pull request here with one new file,
`mods/<id>/<version>.toml`. With the [GitHub CLI](https://cli.github.com) logged in it does it all
itself; otherwise GitHub opens in your browser with the file filled in, and you press Propose new
file and Create pull request. You may write the file by hand too:

```toml
name = "Cogwork"                # shown in the launcher (the newest version's)
summary = "Gears, item tubes and engines."
author = "Zorro909"
repo = "https://github.com/Zorro909/cogwork"
dir = ""                        # the crate's folder in the repository
commit = "3f2a9c1e..."          # the full commit id: exactly what is built
weft = "v26.11.3"               # the Weft release it's built for
deps = []                       # mod ids it needs besides base, installed with it
owner = "Zorro909"              # your GitHub login: the id is yours from now on
reviewed = ""                   # left empty, a maintainer fills it in
```

If the file follows the rules and the mod builds on Windows, Linux and macOS, the pull request is
merged by itself and the mod shows up as not verified a few minutes later.

The rules:

- An id belongs to whoever sent it first. Only they add versions of it.
- A version, once in, stays as it is. To change anything, send a new version.
- A name another mod has is taken.
- `reviewed` is a maintainer's.

## New Weft releases

Almost every Weft release changes what mods are built against, so a build for one release won't
load in the next. For each new release the newest version of every mod is built again, its code
as it was and only the SDK's tag changed. If that builds, the launcher offers it, marked as built
again; if not, the mod waits for its author. A verified build stays verified when built again: the
code is the same.

## For maintainers

- Reading a build's source and finding it fine: set `reviewed = "<your login>"` in its file. Its
  zip doesn't change, only the index does.
- Taking a build down: delete its file, and it's gone from the index. Removing `reviewed` makes it
  not verified again.
- Maintainers are listed in `MAINTAINERS`. Their pull requests may change anything.

How it runs: `check` checks a pull request with main's rules and builds what it adds; `merge`
merges it if that passed, after checking it again; `publish` builds what isn't built yet, one mod
a run, puts each zip in a release here and writes `index.json` to the `gh-pages` branch. A mod's
code runs only in jobs that can't write anything, and alone in its run.
