import os

from helpers import copy_example, paint_stand_ins, tmpdir

import forgekit as fk
import production as P


def test_status_names_the_next_action():
    with tmpdir() as d:
        f = copy_example(d)
        p = P.Prod(os.path.join(f, "production.yaml"))
        st, act = P.next_action(p)
        assert st == "paint"
        assert "prompt passes the lint" in act and "ledger.py prompts" in act
        text = P.cmd_status(p)
        assert "spent" in text and "NEXT:" in text


def test_spend_is_refused_while_a_gate_is_open_and_logged_when_forced():
    with tmpdir() as d:
        f = copy_example(d)
        path = os.path.join(f, "production.yaml")
        assert P.main(["spend", "2.75", "--item", "s03 repaint", "--production", path]) == 1
        before = len(fk.load_yaml(path)["budget"]["spent"])
        assert P.main(["spend", "2.75", "--item", "s03 repaint", "--force", "test", "--production", path]) == 0
        spent = fk.load_yaml(path)["budget"]["spent"]
        assert len(spent) == before + 1 and "forced" in spent[-1]


def test_spend_never_reaches_into_the_reserve():
    with tmpdir() as d:
        f = copy_example(d)
        path = os.path.join(f, "production.yaml")
        assert P.main(["spend", "40", "--item", "too much", "--stage", "style", "--production", path]) == 1


def test_advance_refuses_a_failing_gate_and_signoff_records():
    with tmpdir() as d:
        f = copy_example(d)
        path = os.path.join(f, "production.yaml")
        assert P.main(["advance", path]) == 1
        assert fk.load_yaml(path)["stage"] == "paint"
        assert P.main(["signoff", "motion", "--by", "director", "--note", "watched the preview", "--production", path]) == 0
        assert fk.load_yaml(path)["stages"]["motion"]["signoff"]["by"] == "director"


def test_fixing_the_prompt_clears_the_lint_check():
    with tmpdir() as d:
        f = copy_example(d)
        paint_stand_ins(os.path.join(f, "paintings"), faults=False)
        qa = fk.load_yaml(os.path.join(f, "qa.yaml"))
        corrected = next(e for e in qa["frames"] if e["shot"] == "s03")["repaint"]["corrected_prompt"]
        with open(os.path.join(f, "prompts", "s03.md"), "w") as fh:
            fh.write("# s03\n\n```\n" + corrected.strip() + "\n```\n")
        p = P.Prod(os.path.join(f, "production.yaml"))
        res = P.gate(p, "paint")
        assert res[0][0], res[0]                       # the lint passes with QA's corrected prompt
        st, act = P.next_action(p)
        assert "repaint" in act                         # the next action moves on to the repaint
