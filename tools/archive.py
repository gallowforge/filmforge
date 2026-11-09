#!/usr/bin/env python3
"""archive.py: prove a production folder is complete, today and any day later.

Commands
  build FOLDER [--require LIST] [--require-shotlist S --paintings DIR] [--exclude PATTERN ...]
        Hashes every file (SHA-256) into FOLDER/MANIFEST.sha256 (plain `sha256sum -c` format) and writes
        FOLDER/manifest.json: file count, bytes, what was left out on purpose and why, the required deliverables
        and the digest of the manifest itself. Fails when a required deliverable is missing.
  verify FOLDER [--strict]
        Re-hashes everything and compares: missing, changed and (with --strict) extra files fail.
  compare SRC DST [--exclude PATTERN ...]
        Copy proof: every file under SRC exists under DST with identical bytes.

Examples
  archive.py build my-film --require deliverables.txt --require-shotlist my-film/shotlist.yaml --paintings my-film/paintings
  archive.py verify my-film
  archive.py compare my-film /mnt/backup/my-film
  cd my-film && sha256sum -c MANIFEST.sha256          # the same check without this tool
"""
import argparse
import fnmatch
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forgekit as fk  # noqa: E402

MANIFEST = "MANIFEST.sha256"
META = "manifest.json"
# regenerable or machine-local: left out on purpose, and listed as such in manifest.json
DEFAULT_EXCLUDE = {
    ".git/": "version control internals",
    "__pycache__/": "Python bytecode, regenerated on import",
    ".venv/": "virtual environment, rebuilt from requirements",
    "venv/": "virtual environment, rebuilt from requirements",
    "node_modules/": "packages, reinstalled from the lock file",
    ".DS_Store": "Finder metadata",
    "*.pyc": "Python bytecode",
    "Thumbs.db": "Windows thumbnail cache",
    "*/4k/": "4K upscale cache, rebuilt from the 2K paintings",
}


def _excluded(rel, patterns):
    parts = rel.split("/")
    for pat in patterns:
        if pat.endswith("/"):
            name = pat.rstrip("/")
            if name.startswith("*/"):
                if name[2:] in parts[:-1]:
                    return pat
            elif name in parts[:-1]:
                return pat
        elif fnmatch.fnmatch(parts[-1], pat) or fnmatch.fnmatch(rel, pat):
            return pat
    return None


def walk(folder, patterns):
    files, skipped = [], {}
    for dp, dns, fns in os.walk(folder):
        dns.sort()
        for fn in sorted(fns):
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            if rel in (MANIFEST, META) or os.path.islink(full):
                continue
            pat = _excluded(rel, patterns)
            if pat:
                n, b = skipped.get(pat, (0, 0))
                skipped[pat] = (n + 1, b + os.path.getsize(full))
                continue
            files.append(rel)
    return sorted(files, key=fk.natural_key), skipped


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def hash_all(folder, rels, jobs=None):
    jobs = jobs or min(8, os.cpu_count() or 2)
    with ThreadPoolExecutor(jobs) as ex:
        digests = list(ex.map(lambda r: sha256(os.path.join(folder, r)), rels))
    return dict(zip(rels, digests))


def required_missing(folder, files, req_patterns):
    missing = []
    for pat in req_patterns:
        pat = pat.strip()
        if not pat or pat.startswith("#"):
            continue
        if not any(fnmatch.fnmatch(f, pat) for f in files):
            missing.append(pat)
    return missing


def shotlist_missing(folder, shotlist, paintings):
    sl = fk.load_yaml(shotlist)
    missing = []
    for s in fk.shots_of(sl):
        if s.get("kind", "painting") != "painting":
            continue
        if not fk.find_painting(paintings, s["id"], s.get("painting")):
            missing.append(s["id"])
    return missing


def build(folder, require=None, shotlist=None, paintings=None, exclude=(), jobs=None):
    pats = dict(DEFAULT_EXCLUDE)
    for e in exclude or ():
        pat, _, why = e.partition("=")
        pats[pat] = why or "left out by the archivist"
    files, skipped = walk(folder, pats)
    req = []
    if require:
        req = [line.strip() for line in open(require, encoding="utf-8") if line.strip() and not line.startswith("#")]
    miss = required_missing(folder, files, req)
    miss_shots = shotlist_missing(folder, shotlist, paintings) if shotlist and paintings else []
    digests = hash_all(folder, files, jobs)
    text = "".join(f"{digests[r]}  {r}\n" for r in files)
    with open(os.path.join(folder, MANIFEST), "w", encoding="utf-8") as f:
        f.write(text)
    total = sum(os.path.getsize(os.path.join(folder, r)) for r in files)
    kinds = {}
    for r in files:
        ext = os.path.splitext(r)[1].lower() or "(none)"
        kinds[ext] = kinds.get(ext, 0) + 1
    meta = dict(tool="archive", version=1, files=len(files), bytes=total,
                manifest_sha256=hashlib.sha256(text.encode()).hexdigest(),
                by_type=dict(sorted(kinds.items(), key=lambda kv: -kv[1])),
                left_out=[dict(pattern=k, why=pats[k], files=v[0], bytes=v[1]) for k, v in skipped.items()],
                required=req, required_missing=miss, shots_missing=miss_shots,
                complete=not miss and not miss_shots)
    with open(os.path.join(folder, META), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    return meta


def verify(folder, strict=False, jobs=None):
    mpath = os.path.join(folder, MANIFEST)
    if not os.path.exists(mpath):
        fk.die(f"no {MANIFEST} in {folder}: run archive.py build first")
    want = {}
    for line in open(mpath, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line:
            continue
        h, rel = line.split("  ", 1)
        want[rel] = h
    meta = {}
    if os.path.exists(os.path.join(folder, META)):
        meta = json.load(open(os.path.join(folder, META)))
        text = open(mpath, encoding="utf-8").read()
        if meta.get("manifest_sha256") and hashlib.sha256(text.encode()).hexdigest() != meta["manifest_sha256"]:
            return dict(ok=False, tampered_manifest=True, missing=[], changed=[], extra=[], checked=0)
    pats = dict(DEFAULT_EXCLUDE)
    for lo in meta.get("left_out", []):
        pats.setdefault(lo["pattern"], lo["why"])
    have, _ = walk(folder, pats)
    present = [r for r in want if os.path.exists(os.path.join(folder, r))]
    missing = [r for r in want if r not in set(present)]
    got = hash_all(folder, present, jobs)
    changed = [r for r in present if got[r] != want[r]]
    extra = [r for r in have if r not in want]
    ok = not missing and not changed and not (strict and extra)
    return dict(ok=ok, tampered_manifest=False, missing=missing, changed=changed, extra=extra, checked=len(present),
                required_missing=meta.get("required_missing", []), complete=meta.get("complete"))


def compare(src, dst, exclude=(), jobs=None):
    pats = dict(DEFAULT_EXCLUDE)
    for e in exclude or ():
        pats[e] = "excluded"
    files, _ = walk(src, pats)
    missing = [r for r in files if not os.path.exists(os.path.join(dst, r))]
    both = [r for r in files if r not in set(missing)]
    a = hash_all(src, both, jobs)
    b = hash_all(dst, both, jobs)
    differ = [r for r in both if a[r] != b[r]]
    return dict(ok=not missing and not differ, files=len(files), missing=missing, differ=differ)


def _human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024.0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="hash a production folder and record what is required")
    b.add_argument("folder")
    b.add_argument("--require", help="text file of glob patterns (relative to FOLDER) that must each match a file")
    b.add_argument("--require-shotlist", help="every painting shot in this shot list must have its painting")
    b.add_argument("--paintings", help="folder holding the paintings (for --require-shotlist)")
    b.add_argument("--exclude", action="append", default=[], help="pattern to leave out, optionally PATTERN=why (repeatable)")
    b.add_argument("--jobs", type=int, help="hashing threads")
    v = sub.add_parser("verify", help="re-hash and compare with the manifest")
    v.add_argument("folder")
    v.add_argument("--strict", action="store_true", help="files not in the manifest fail too")
    v.add_argument("--jobs", type=int)
    c = sub.add_parser("compare", help="prove DST is a byte-exact copy of SRC")
    c.add_argument("src")
    c.add_argument("dst")
    c.add_argument("--exclude", action="append", default=[])
    c.add_argument("--jobs", type=int)
    a = p.parse_args(argv)
    if a.cmd == "build":
        if a.require_shotlist and not a.paintings:
            fk.die("--require-shotlist needs --paintings")
        m = build(a.folder, a.require, a.require_shotlist, a.paintings, a.exclude, a.jobs)
        print(f"{m['files']} files, {_human(m['bytes'])} hashed into {os.path.join(a.folder, MANIFEST)}")
        for lo in m["left_out"]:
            print(f"  left out on purpose: {lo['pattern']} ({fk.plural(lo['files'], 'file')}, {_human(lo['bytes'])}): {lo['why']}")
        if m["required"]:
            print(f"  required deliverables: {len(m['required']) - len(m['required_missing'])}/{len(m['required'])} present")
        for r in m["required_missing"]:
            print(f"  MISSING required: {r}")
        for s in m["shots_missing"]:
            print(f"  MISSING painting for shot {s}")
        print(f"manifest digest {m['manifest_sha256'][:16]}...  " + ("COMPLETE" if m["complete"] else "INCOMPLETE"))
        return 0 if m["complete"] else 1
    if a.cmd == "verify":
        r = verify(a.folder, a.strict, a.jobs)
        if r["tampered_manifest"]:
            print("FAIL: MANIFEST.sha256 does not match the digest recorded in manifest.json (the manifest was edited)")
            return 1
        for x in r["missing"]:
            print(f"MISSING  {x}")
        for x in r["changed"]:
            print(f"CHANGED  {x}")
        for x in r["extra"]:
            print(f"{'EXTRA' if a.strict else 'new'}      {x}")
        state = "OK" if r["ok"] else "FAIL"
        print(f"{state}: {r['checked']} files checked, {len(r['missing'])} missing, {len(r['changed'])} changed, "
              f"{len(r['extra'])} not in the manifest" + ("" if r.get("complete", True) else "; the build recorded missing deliverables"))
        return 0 if r["ok"] and r.get("complete", True) is not False else 1
    if a.cmd == "compare":
        r = compare(a.src, a.dst, a.exclude, a.jobs)
        for x in r["missing"]:
            print(f"MISSING in copy  {x}")
        for x in r["differ"]:
            print(f"DIFFERENT        {x}")
        print(("OK" if r["ok"] else "FAIL") + f": {r['files']} files, {len(r['missing'])} missing, {len(r['differ'])} different")
        return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
