#!/usr/bin/env python3
"""
Skill: agile-github-breakdown
Regression tests for parse_frnfr.py and validate_story_graph.py.

Stdlib `unittest` only — no pytest, no third-party deps, nothing to install, matching the
"python3 stdlib only" constraint the scripts themselves follow. Run from anywhere:

  python3 .agents/skills/agile-github-breakdown/scripts/test_skill_scripts.py

`unittest discover` does not work here: it requires an importable start directory, and
`.agents` is not a valid package path segment. Run the file directly.

**Deliberately not wired into CI** — skills are not production code. This is a manual
authoring aid, run by hand when someone edits either script.

Note what is *absent*: there are no Markdown table-shape tests any more. `parse_frnfr`
used to discover tables inside an arbitrary Markdown document, and eleven review rounds each
found another way for that discovery to silently return the wrong requirements — fenced
examples, block quotes, list items, ragged rows, indentation, fence-closing rules. Narrowing
the input contract to an explicit `<ID> | <text>` list deleted that surface, and with it
about thirty tests that only existed to pin down CommonMark corner cases.
"""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parse_frnfr = load("parse_frnfr")
validate_story_graph = load("validate_story_graph")


def run_script(name, payload, *args):
    """Run a script with payload on stdin; return (exit_code, stdout, stderr)."""
    # argv list, shell=False (default): sys.executable plus a sibling script name from
    # this directory. Payload is stdin, never interpolated into the command.
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / f"{name}.py"), *args],
        input=payload,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class ParseRequirementsContract(unittest.TestCase):
    """One requirement per line, `<ID> | <text>`. Nothing else is input."""

    def parse(self, text, prefixes=None):
        return parse_frnfr.parse(text, prefixes)

    def test_single_requirement(self):
        reqs, dups, problems = self.parse("FR-1 | System must do X\n")
        self.assertEqual(reqs, {"FR-1": "System must do X"})
        self.assertEqual((dups, problems), ([], []))

    def test_multiple_requirements(self):
        reqs, _, problems = self.parse("FR-1 | one\nNFR-11 | two\n")
        self.assertEqual(reqs, {"FR-1": "one", "NFR-11": "two"})
        self.assertEqual(problems, [])

    def test_blank_lines_are_ignored(self):
        reqs, _, problems = self.parse("\nFR-1 | one\n\n\nFR-2 | two\n\n")
        self.assertEqual(reqs, {"FR-1": "one", "FR-2": "two"})
        self.assertEqual(problems, [])

    def test_surrounding_whitespace_is_trimmed(self):
        reqs, _, _ = self.parse("   FR-1   |   spaced out   \n")
        self.assertEqual(reqs, {"FR-1": "spaced out"})

    def test_text_may_contain_pipes(self):
        # Split on the first pipe only, so no escaping rule is needed.
        reqs, _, _ = self.parse("NFR-1 | p95 < 5s | p99 < 8s\n")
        self.assertEqual(reqs, {"NFR-1": "p95 < 5s | p99 < 8s"})

    def test_measurable_bar_is_preserved_verbatim(self):
        reqs, _, _ = self.parse("NFR-9 | p95 < 5s\n")
        self.assertEqual(reqs["NFR-9"], "p95 < 5s")

    def test_duplicate_id_keeps_first_and_reports_it(self):
        reqs, dups, problems = self.parse("FR-1 | first\nFR-1 | second\n")
        self.assertEqual(reqs, {"FR-1": "first"})
        self.assertEqual(dups, ["FR-1"])
        self.assertEqual(problems, [])


class ParseRequirementsMalformedInput(unittest.TestCase):
    """A dropped requirement is invisible downstream, so nothing is skipped silently."""

    def problems(self, text, prefixes=None):
        return parse_frnfr.parse(text, prefixes)[2]

    def test_line_without_a_pipe_is_an_error(self):
        problems = self.problems("FR-1 the pipe is missing\n")
        self.assertEqual(len(problems), 1)
        self.assertIn("line 1", problems[0])

    def test_prose_line_is_an_error_not_a_silent_skip(self):
        # The old parser quietly ignored anything it did not recognise as a row, which is how
        # requirements went missing while the command still succeeded.
        self.assertEqual(len(self.problems("Some notes about FR-1 | and a pipe\n")), 1)

    def test_wrapped_id_is_an_error(self):
        # The caller writes this line, so it writes a bare ID. Accepting `**FR-1**` or
        # `[FR-1](...)` would reopen the "what counts as an ID cell" question for no gain.
        for cell in ["**FR-1**", "[FR-1](#fr-1)", "`FR-1`"]:
            with self.subTest(cell=cell):
                self.assertEqual(len(self.problems(f"{cell} | text\n")), 1)

    def test_lowercase_id_is_an_error(self):
        self.assertEqual(len(self.problems("fr-1 | text\n")), 1)

    def test_missing_text_is_an_error(self):
        problems = self.problems("FR-1 |\n")
        self.assertEqual(len(problems), 1)
        self.assertIn("no requirement text", problems[0])

    def test_error_names_every_offending_line(self):
        problems = self.problems("FR-1 | ok\nbroken line\nFR-2 | ok\nalso broken\n")
        self.assertEqual(len(problems), 2)
        self.assertIn("line 2", problems[0])
        self.assertIn("line 4", problems[1])

    def test_filtered_prefix_is_not_an_error(self):
        # Deliberately excluded, as opposed to malformed: no problem is recorded.
        reqs, _, problems = parse_frnfr.parse("EXT-350 | an external key\n", ["FR", "NFR"])
        self.assertEqual((reqs, problems), ({}, []))


class ParseRequirementsExitCodes(unittest.TestCase):
    """0 parsed, 1 nothing matched, 2 malformed. The workflow branches on these."""

    def test_success(self):
        code, out, _ = run_script("parse_frnfr", "FR-1 | x\n", "--prefix", "FR")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["requirements"], [{"id": "FR-1", "text": "x"}])

    def test_malformed_input_exits_2(self):
        code, _, err = run_script("parse_frnfr", "not a requirement\n")
        self.assertEqual(code, 2)
        self.assertIn("malformed requirement list", err)

    def test_zero_matches_exits_1(self):
        code, _, err = run_script("parse_frnfr", "EXT-350 | noise\n", "--prefix", "FR", "NFR")
        self.assertEqual(code, 1)
        self.assertIn("no requirements", err)

    def test_empty_input_exits_1(self):
        self.assertEqual(run_script("parse_frnfr", "\n\n")[0], 1)

    def test_prefix_requires_at_least_one_value(self):
        # nargs="*" would let a bare `--prefix` yield [], which is falsy and would silently
        # disable both the filter and the zero-match hard stop.
        code, _, err = run_script("parse_frnfr", "FR-1 | x\n", "--prefix")
        self.assertEqual(code, 2)
        self.assertIn("expected at least one argument", err)

    def test_output_is_sorted_numerically_not_lexically(self):
        # The reason this is a script and not eyeballed: FR-10 sorts after FR-9.
        _, out, _ = run_script("parse_frnfr", "FR-10 | ten\nFR-9 | nine\nFR-1 | one\n")
        self.assertEqual([r["id"] for r in json.loads(out)["requirements"]], ["FR-1", "FR-9", "FR-10"])

    def test_duplicate_warning_goes_to_stderr_without_failing(self):
        code, _, err = run_script("parse_frnfr", "FR-1 | first\nFR-1 | second\n")
        self.assertEqual(code, 0)
        self.assertIn("duplicate", err)

    def test_no_syntax_warning_on_import(self):
        result = subprocess.run(
            [sys.executable, "-W", "error::SyntaxWarning", str(SCRIPTS / "parse_frnfr.py")],
            input="FR-1 | x\n", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")


class ValidateStoryGraphExitCodes(unittest.TestCase):
    """0 = clean, 1 = graph failed validation, 2 = input unreadable. Consumers branch on this."""

    def code(self, payload, *args):
        return run_script("validate_story_graph", json.dumps(payload), *args)[0]

    def test_clean_graph(self):
        self.assertEqual(self.code({"requirement_ids": ["FR-1"], "stories": [{"key": "S1", "ac_ids": ["FR-1"]}]}), 0)

    def test_cycle(self):
        self.assertEqual(self.code({"stories": [
            {"key": "S1", "depends_on": ["S2"]}, {"key": "S2", "depends_on": ["S1"]}]}), 1)

    def test_dangling_dependency(self):
        self.assertEqual(self.code({"stories": [{"key": "S1", "depends_on": ["S9"]}]}), 1)

    def test_known_external_exempts_a_dependency(self):
        payload = {"stories": [{"key": "S1", "depends_on": ["#42"]}]}
        self.assertEqual(self.code(payload, "--known-external", "#42"), 0)

    def test_duplicate_story_keys(self):
        self.assertEqual(self.code({"stories": [{"key": "S1"}, {"key": "S1"}]}), 1)

    def test_unknown_ac_id(self):
        self.assertEqual(self.code({"requirement_ids": ["FR-1"], "stories": [{"key": "S1", "ac_ids": ["FR-99"]}]}), 1)

    def test_absent_requirement_ids_disables_the_unknown_check(self):
        self.assertEqual(self.code({"stories": [{"key": "S1", "ac_ids": ["FR-1"]}]}), 0)

    def test_missing_coverage_is_only_a_warning(self):
        self.assertEqual(self.code({"requirement_ids": ["FR-1", "FR-2"], "stories": [{"key": "S1", "ac_ids": ["FR-1"]}]}), 0)


class ValidateStoryGraphMalformedInput(unittest.TestCase):
    """Absence and wrong types must fail loudly, never read as an empty-but-valid graph."""

    def problems(self, data):
        return validate_story_graph.check_input(data)

    def code(self, payload):
        return run_script("validate_story_graph", json.dumps(payload))[0]

    def test_absent_stories_member_is_rejected(self):
        self.assertEqual(self.code({"requirement_ids": ["FR-1"]}), 2)

    def test_explicit_empty_stories_list_is_valid(self):
        self.assertEqual(self.code({"requirement_ids": ["FR-1"], "stories": []}), 0)

    def test_stories_not_a_list(self):
        self.assertEqual(self.code({"stories": {"key": "S1"}}), 2)

    def test_top_level_not_an_object(self):
        self.assertEqual(self.code([{"key": "S1"}]), 2)

    def test_invalid_json(self):
        self.assertEqual(run_script("validate_story_graph", '{"stories":')[0], 2)

    def test_story_without_a_key(self):
        self.assertEqual(self.code({"stories": [{"depends_on": []}]}), 2)

    def test_story_key_must_be_a_string(self):
        self.assertTrue(self.problems({"stories": [{"key": 1}]}))

    def test_requirement_ids_as_a_string_is_rejected(self):
        # set("FR-12") == set("FR-21") — a string compares as a character set, so coverage
        # diffs come back empty and the run reports all-clear on malformed input.
        self.assertEqual(self.code({"requirement_ids": "FR-12", "stories": [{"key": "S1", "ac_ids": ["FR-1"]}]}), 2)

    def test_ac_ids_as_a_string_is_rejected(self):
        self.assertEqual(self.code({"requirement_ids": ["FR-12"], "stories": [{"key": "S1", "ac_ids": "FR-21"}]}), 2)

    def test_depends_on_as_a_string_is_rejected(self):
        # Would otherwise yield one dangling entry per character.
        self.assertEqual(self.code({"stories": [{"key": "S1", "depends_on": "S2"}, {"key": "S2"}]}), 2)

    def test_non_string_inside_a_list_is_rejected(self):
        self.assertEqual(self.code({"requirement_ids": ["FR-1", 2], "stories": [{"key": "S1"}]}), 2)

    def test_message_names_the_offending_index(self):
        problems = self.problems({"stories": [{"depends_on": []}, {"key": "S2"}, 42]})
        self.assertEqual(len(problems), 2)
        self.assertIn("stories[0]", problems[0])
        self.assertIn("stories[2]", problems[1])


class ValidateStoryGraphReport(unittest.TestCase):
    def report(self, data, known_external=()):
        return validate_story_graph.build_report(data, set(known_external))

    def test_missing_coverage_lists_uncited_requirements(self):
        got = self.report({"requirement_ids": ["FR-1", "FR-2"], "stories": [{"key": "S1", "ac_ids": ["FR-1"]}]})
        self.assertEqual(got["missing_coverage"], ["FR-2"])

    def test_subnumber_suggestion_for_a_stub_consumer_pair(self):
        got = self.report({"stories": [{"key": "S1"}, {"key": "S2", "depends_on": ["S1"]}]})
        self.assertEqual(got["subnumber_suggestions"], [["S1", "S2"]])

    def test_no_suggestion_when_two_stories_share_a_dependency(self):
        got = self.report({"stories": [
            {"key": "S1"}, {"key": "S2", "depends_on": ["S1"]}, {"key": "S3", "depends_on": ["S1"]}]})
        self.assertEqual(got["subnumber_suggestions"], [])


class ParserPipelineIntegration(unittest.TestCase):
    """parse_frnfr output must feed validate_story_graph unchanged."""

    def test_requirement_ids_flow_into_the_validator(self):
        _, out, _ = run_script("parse_frnfr", "FR-1 | one\nFR-2 | two\n", "--prefix", "FR")
        ids = [r["id"] for r in json.loads(out)["requirements"]]
        payload = {"requirement_ids": ids, "stories": [{"key": "S1", "ac_ids": ["FR-1"]}]}
        code, report, _ = run_script("validate_story_graph", json.dumps(payload))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(report)["missing_coverage"], ["FR-2"])


create_github_breakdown = load("create_github_breakdown")


class CreateGithubBreakdownHelpers(unittest.TestCase):
    def test_heading_without_table_still_stamps(self):
        body = "## Translation (AI context)\n\nplaceholder only\n"
        out = create_github_breakdown.ensure_translation_table(body)
        self.assertIn(create_github_breakdown.TRANSLATION_TABLE_MARKER, out)
        self.assertEqual(out.count("## Translation (AI context)"), 1)

    def test_existing_table_is_not_duplicated(self):
        body = create_github_breakdown.TRANSLATION_TABLE
        out = create_github_breakdown.ensure_translation_table(body)
        self.assertEqual(out.count(create_github_breakdown.TRANSLATION_TABLE_MARKER), 1)

    def test_pipe_in_title_is_escaped(self):
        table = create_github_breakdown.build_tasks_table(
            [{"key": "S1", "number": 7, "title": "Support A | B"}]
        )
        self.assertIn(r"Support A \| B", table)

    def test_adjacent_heading_is_kept(self):
        body = "## Tasks\n\n| Key | Issue | Title |\n|-----|-------|-------|\n| S1 | #1 | old |\n## Open questions\n- leftover\n"
        out = create_github_breakdown.ensure_tasks_table(
            body, [{"key": "S2", "number": 2, "title": "new"}]
        )
        self.assertIn("## Open questions", out)
        self.assertIn("#2", out)

    def test_merge_keeps_prior_keys(self):
        existing = [{"key": "S1", "number": 1, "title": "old"}]
        created = [{"key": "S2", "number": 2, "title": "new"}]
        merged = create_github_breakdown.merge_created(existing, created)
        self.assertEqual([row["key"] for row in merged], ["S1", "S2"])

    def test_string_depends_on_is_rejected(self):
        with self.assertRaises(RuntimeError):
            create_github_breakdown.validate_tasks(
                [{"key": "S1", "title": "one", "depends_on": "S2"}]
            )

    def test_duplicate_key_is_rejected(self):
        with self.assertRaises(RuntimeError):
            create_github_breakdown.validate_tasks(
                [{"key": "S1", "title": "one"}, {"key": "S1", "title": "two"}]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
