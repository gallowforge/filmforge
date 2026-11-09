#!/usr/bin/env python3
"""Run the real tools on the worked example and write each output as a terminal page for the README visuals.

Nothing in a terminal image is typed by hand: every line is what the tools print when they run on
examples/the-lantern-moth today. The pages go to docs/readme/build/pages, where capture.cjs photographs them.

usage: python3 docs/readme/src/terminals.py
"""
import html
import re
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parents[2]
EXAMPLE = ROOT / 'examples' / 'the-lantern-moth'
OUT = SRC.parent / 'build' / 'pages'
PROMPT = 'the-lantern-moth $'
CSS = (SRC / 'pages' / 'term.css').read_text(encoding='utf-8')

# (page, width in CSS px, extra body class, commands); a command is (tool, args)
LINT = ('ledger', ['prompts', 'continuity.yaml', '--prompts', 'prompts', '--style', 'style-lock.yaml', '--shotlist', 'shotlist.yaml'])
TERMINALS = [
    ('term-budget', 820, '', [('budget', ['shotlist.yaml', '--production', 'production.yaml'])]),
    ('term-lint', 700, 'wrap', [LINT]),
    ('term-gate', 760, 'wrap', [('production', ['gate', '--production', 'production.yaml'])]),
    ('term-shotlist', 600, '', [('shotlist', ['validate', 'shotlist.yaml', '--ledger', 'continuity.yaml']),
                                ('shotlist', ['stats', 'shotlist.yaml'])]),
    ('term-status', 640, '', [('production', ['status', 'production.yaml'])]),
]

# colour by meaning only: green passes, ember fails, gold marks where you are and what is open
RULES = [
    (re.compile(r'^(ERROR)(\s.*)$'), lambda m: f'<span class="err">{m[1]}</span><span class="b">{m[2]}</span>', 'err'),
    (re.compile(r'^(FITS:)(.*)$'), lambda m: f'<span class="ok">{m[1]}</span><span class="b">{m[2]}</span>', 'fits'),
    (re.compile(r'^(ok:)(.*)$'), lambda m: f'<span class="ok">{m[1]}</span><span class="b">{m[2]}</span>', 'ok'),
    (re.compile(r'^(NEXT:)(.*)$'), lambda m: f'<span class="acc">{m[1]}</span><span class="b">{m[2]}</span>', 'next'),
    (re.compile(r'^(gate \'\w+\': )(FAIL)$'), lambda m: f'<span class="b">{m[1]}</span><span class="err">{m[2]}</span>', 'gate'),
    (re.compile(r'^(\[x\])(.*)$'), lambda m: f'<span class="ok">{m[1]}</span>{m[2]}', None),
    (re.compile(r'^(\[ \])(.*)$'), lambda m: f'<span class="acc">{m[1]}</span><span class="b">{m[2]}</span>', None),
    (re.compile(r'^(\s+do:.*)$'), lambda m: f'<span class="d">{m[1]}</span>', None),
    (re.compile(r'^(-[- ]+)$'), lambda m: f'<span class="d">{m[1]}</span>', None),
    (re.compile(r'^(.*)(&lt;- here)(.*)$'), lambda m: f'<span class="b">{m[1]}</span><span class="acc">{m[2]}</span>{m[3]}', None),
    (re.compile(r'^(.*\(stage: )(\w+)(\).*)$'), lambda m: f'<span class="b">{m[1]}</span><span class="acc">{m[2]}</span><span class="b">{m[3]}</span>', None),
    (re.compile(r'^(continuity: )(ok)$'), lambda m: f'{m[1]}<span class="ok">{m[2]}</span>', None),
]


def run(tool, args):
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / f'{tool}.py'), *args], cwd=EXAMPLE,
                       capture_output=True, text=True, check=False)
    return (r.stdout + r.stderr).rstrip('\n')


def line_html(text):
    esc = html.escape(text, quote=False)
    for rx, fmt, lift in RULES:
        m = rx.match(esc)
        if m:
            attr = f' data-lift="{lift}"' if lift else ''
            return f'<div class="l"{attr}>{fmt(m)}</div>'
    return f'<div class="l">{esc}</div>' if esc else '<div class="l"> </div>'


def fits(row):
    return row.replace('(fits)', '<span class="ok">(fits)</span>')


def page(width, cls, body):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="size" content="{width}">\n'
            f'<style>\n{CSS}</style></head>\n<body class="term {cls}">\n{body}\n</body></html>\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, width, cls, cmds in TERMINALS:
        parts = []
        for i, (tool, args) in enumerate(cmds):
            if i:
                parts.append('<div class="gap"></div>')
            cmd = html.escape(' '.join([f'{tool}.py', *args]))
            parts.append(f'<div class="l cmdline"><span class="p">{PROMPT}</span> <span class="c">{cmd}</span></div>')
            parts += [fits(line_html(t)) for t in run(tool, args).splitlines()]
        parts.append(f'<div class="l"><span class="p">{PROMPT}</span> <span class="cur"></span></div>')
        (OUT / f'{name}.html').write_text(page(width, cls, '\n'.join(parts)), encoding='utf-8')
        print('wrote', (OUT / f'{name}.html').relative_to(ROOT))

    # one shot of the shot list as it is on disk: s05, the beam, whose whole life is four lines of motion
    text = (EXAMPLE / 'shotlist.yaml').read_text(encoding='utf-8')
    block = re.search(r'^  - id: s05\n(?:    .*\n|\n(?=    ))*', text, re.M)[0].rstrip('\n')
    rows = []
    for t in block.splitlines():
        esc = html.escape(t, quote=False)
        esc = re.sub(r'^(\s*-?\s*)([\w_]+)(:)', r'\1<span class="k">\2</span><span class="d">\3</span>', esc)
        lift = ' data-lift="motion"' if t.strip() == 'motion:' else ''
        rows.append(f'<div class="l"{lift}>{esc}</div>')
    body = '<div class="l"><span class="d"># examples/the-lantern-moth/shotlist.yaml</span></div>\n' + '\n'.join(rows)
    (OUT / 'yaml-shot.html').write_text(page(470, 'yaml', body), encoding='utf-8')
    print('wrote', (OUT / 'yaml-shot.html').relative_to(ROOT))


if __name__ == '__main__':
    main()
