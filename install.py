#!/usr/bin/env python3
"""install.py: install the FilmForge skills into a Claude skills folder.

Each skill is installed self-contained: its SKILL.md and references/, plus the tools in scripts/, the price table in
config/ and the templates in templates/, so every skill can run every check from its own folder.

  python3 install.py                       # into ~/.claude/skills
  python3 install.py --dest path/to/skills
  python3 install.py --dry-run             # show what would happen
  python3 install.py --uninstall           # remove only the forge-* folders this installer created

Safety: a folder is replaced only if it carries this installer's marker (.forge-engine). Any other folder with the
same name is left alone and reported. Nothing outside the forge-* folders is touched.
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = ".forge-engine"


def skills():
    base = os.path.join(HERE, "skills")
    return sorted(d for d in os.listdir(base) if d.startswith("forge-") and os.path.exists(os.path.join(base, d, "SKILL.md")))


def owned(path):
    return os.path.exists(os.path.join(path, MARKER))


def install_one(name, dest, dry):
    src = os.path.join(HERE, "skills", name)
    dst = os.path.join(dest, name)
    if os.path.exists(dst) and not owned(dst):
        return f"skipped {dst}: exists and was not made by this installer"
    if dry:
        return f"would install {dst}"
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    shutil.copy2(os.path.join(src, "SKILL.md"), dst)
    if os.path.isdir(os.path.join(src, "references")):
        shutil.copytree(os.path.join(src, "references"), os.path.join(dst, "references"))
    os.makedirs(os.path.join(dst, "scripts"))
    for f in sorted(os.listdir(os.path.join(HERE, "tools"))):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(HERE, "tools", f), os.path.join(dst, "scripts", f))
            if f != "forgekit.py":
                os.chmod(os.path.join(dst, "scripts", f), 0o755)
    shutil.copytree(os.path.join(HERE, "config"), os.path.join(dst, "config"))
    shutil.copytree(os.path.join(HERE, "templates"), os.path.join(dst, "templates"))
    files = sorted(os.path.relpath(os.path.join(dp, f), dst) for dp, _, fs in os.walk(dst) for f in fs)
    with open(os.path.join(dst, MARKER), "w") as fh:
        json.dump({"engine": "filmforge", "skill": name, "files": files}, fh, indent=1)
    return f"installed {dst} ({len(files)} files)"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dest", default=os.path.expanduser("~/.claude/skills"), help="skills folder (default ~/.claude/skills)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--uninstall", action="store_true")
    a = p.parse_args(argv)
    os.makedirs(a.dest, exist_ok=True)
    for name in skills():
        dst = os.path.join(a.dest, name)
        if a.uninstall:
            if owned(dst):
                if not a.dry_run:
                    shutil.rmtree(dst)
                print(("would remove " if a.dry_run else "removed ") + dst)
            elif os.path.exists(dst):
                print(f"left {dst}: not made by this installer")
            continue
        print(install_one(name, a.dest, a.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
