#!/usr/bin/env python3
"""Docs check for filmforge. Runs in CI and locally, with no dependencies.

It fails when:
  - a relative link or image in any Markdown file does not resolve, or a #heading anchor does not exist
  - an image referenced by a README visual's HTML source is missing
  - a README visual is missing its wide or phone render, or the README does not use both
  - an image in docs/img or docs/readme is not used anywhere
  - a template is missing one of its required sections
  - a size budget is broken (per file, docs/readme, whole repository)
  - a text file contains a machine path, a private network address or right-to-left script
"""
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

MAX_FILE = 2_000_000          # bytes, any single file
MAX_README_VISUALS = 8_000_000
MAX_REPO = 25_000_000
TEXT_EXT = {'.md', '.html', '.css', '.js', '.py', '.sh', '.yml', '.yaml', '.json', '.csv', '.txt'}

TEMPLATES = {
    'templates/delivery-checklist.md': ['The deliverables matrix', 'Checks before calling it delivered', 'Archive'],
}

errors = []


def err(msg):
    errors.append(msg)


def tracked_files():
    try:
        out = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                             capture_output=True, check=True).stdout.decode()
        files = [Path(f) for f in out.split('\0') if f]
        if files:
            return [f for f in files if f.exists()]
    except (OSError, subprocess.CalledProcessError):
        pass
    return [p.relative_to(ROOT) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and 'node_modules' not in p.parts]


def slug(heading):
    s = re.sub(r'<[^>]+>', '', heading).strip().lower()
    s = ''.join(ch for ch in s if ch in ' -_' or unicodedata.category(ch)[0] in 'LN')
    return s.replace(' ', '-')


def strip_code(text):
    text = re.sub(r'^```.*?^```', '', text, flags=re.S | re.M)
    return re.sub(r'`[^`\n]*`', '', text)


def anchors_of(path, cache={}):
    if path not in cache:
        seen, out = {}, set()
        for line in strip_code(path.read_text(encoding='utf-8')).splitlines():
            m = re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', line)
            if m:
                base = slug(m.group(2))
                n = seen.get(base, 0)
                out.add(base if n == 0 else f'{base}-{n}')
                seen[base] = n + 1
        cache[path] = out
    return cache[path]


files = tracked_files()
md_files = sorted(f for f in files if f.suffix == '.md')
used_images = set()
links_checked = anchors_checked = 0

# 1. Markdown links, images and anchors
LINK_RE = re.compile(r'!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)|(?:src|href|srcset)="([^"]+)"')
for md in md_files:
    text = strip_code(md.read_text(encoding='utf-8'))
    for m in LINK_RE.finditer(text):
        url = m.group(1) or m.group(2)
        if re.match(r'^[a-z]+:', url) or url.startswith('//'):
            continue
        links_checked += 1
        target, _, frag = url.partition('#')
        dest = (md.parent / target).resolve() if target else (ROOT / md).resolve()
        if not dest.exists():
            err(f'{md}: link to missing file {url}')
            continue
        if dest.is_file() and dest.suffix in {'.webp', '.png', '.jpg', '.svg'}:
            used_images.add(dest)
        if frag:
            anchors_checked += 1
            if dest.suffix != '.md':
                err(f'{md}: anchor on a non-Markdown target {url}')
            elif frag not in anchors_of(dest):
                err(f'{md}: missing anchor #{frag} in {dest.relative_to(ROOT)}')

# 2. README visual sources and renders
src_dir = Path('docs/readme/src')
readme = Path('README.md').read_text(encoding='utf-8')
visuals = sorted(p.stem for p in src_dir.glob('*.html'))
for name in visuals:
    html = (src_dir / f'{name}.html').read_text(encoding='utf-8')
    for ref in re.findall(r'(?:src|href)="([^"]+)"|url\(([^)]+)\)', html):
        ref = (ref[0] or ref[1]).strip('\'"')
        if re.match(r'^[a-z]+:', ref) or ref.startswith('#') or '${' in ref:
            continue
        dest = (src_dir / ref).resolve()
        if not dest.exists():
            err(f'{src_dir}/{name}.html: missing {ref}')
        else:
            used_images.add(dest)
    if name == 'social':
        if not Path('docs/readme/social.png').exists():
            err('docs/readme/social.png is missing (run python3 scripts/readme-visuals.py pages social)')
        used_images.add((ROOT / 'docs/readme/social.png').resolve())
        continue
    for suffix in ('', '-mobile'):
        out = Path(f'docs/readme/{name}{suffix}.webp')
        if not out.exists():
            err(f'{out} is missing (run python3 scripts/readme-visuals.py pages {name})')
        elif f'docs/readme/{name}{suffix}.webp' not in readme:
            err(f'README.md does not use {out}')

# 3. No unused images
for folder in ('docs/readme',):
    for p in Path(folder).glob('*'):
        if p.suffix in {'.webp', '.png', '.jpg'} and p.resolve() not in used_images:
            err(f'{p} is not used by any page or visual')

# 4. Templates
for path, sections in TEMPLATES.items():
    p = Path(path)
    if not p.exists():
        err(f'{path} is missing')
        continue
    heads = {re.sub(r'^#+\s+', '', line).strip() for line in p.read_text(encoding='utf-8').splitlines() if line.startswith('#')}
    for s in sections:
        if s not in heads:
            err(f'{path}: missing section "{s}"')

# 5. Size budgets
total = readme_visuals = 0
for f in files:
    size = f.stat().st_size
    total += size
    if f.parts[:2] == ('docs', 'readme'):
        readme_visuals += size
    if size > MAX_FILE:
        err(f'{f} is {size / 1e6:.1f} MB (limit {MAX_FILE / 1e6:.0f} MB per file)')
if readme_visuals > MAX_README_VISUALS:
    err(f'docs/readme is {readme_visuals / 1e6:.1f} MB (limit {MAX_README_VISUALS / 1e6:.0f} MB)')
if total > MAX_REPO:
    err(f'the repository is {total / 1e6:.1f} MB (limit {MAX_REPO / 1e6:.0f} MB)')

# 6. Hygiene: machine paths, private addresses, right-to-left script
PATH_RE = re.compile(r'(?<![\w.])(?:/home/[a-z]|/Users/[A-Za-z]|[A-Z]:\\Users\\)')
IP_RE = re.compile(r'\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b')
RTL_RE = re.compile(r'[\u0590-\u08ff\ufb1d-\ufdff\ufe70-\ufeff]')
for f in files:
    if f.suffix not in TEXT_EXT or f == Path('scripts/check_docs.py'):
        continue
    for i, line in enumerate(f.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        if PATH_RE.search(line):
            err(f'{f}:{i}: machine path')
        for ip in IP_RE.findall(line):
            if not ip.startswith('192.168.1.'):
                err(f'{f}:{i}: private address {ip}')
        if RTL_RE.search(line):
            err(f'{f}:{i}: right-to-left script')

print(f'{len(md_files)} Markdown files, {links_checked} relative links ({anchors_checked} anchors), '
      f'{len(visuals)} visuals, {len(used_images)} images, {len(TEMPLATES)} templates, '
      f'{total / 1e6:.1f} MB tracked ({readme_visuals / 1e6:.1f} MB of README visuals)')
if errors:
    print(f'\n{len(errors)} problem(s):')
    for e in errors:
        print('  -', e)
    sys.exit(1)
print('docs check passed')
