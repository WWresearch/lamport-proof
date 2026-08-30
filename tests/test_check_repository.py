from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import check_repository


class RepositoryCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "lamport-proof"
        self.root.mkdir()
        for directory in (".codex-plugin", ".github", "evals", "scripts", "skills"):
            shutil.copytree(REPOSITORY_ROOT / directory, self.root / directory)
        for filename in (
            "CHANGELOG.md",
            "CITATION.cff",
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "LICENSE",
            "PROVENANCE.md",
            "README.md",
            "SECURITY.md",
        ):
            shutil.copy2(REPOSITORY_ROOT / filename, self.root / filename)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def inspect_fixture(self) -> list[str]:
        errors, _ = check_repository.inspect_tree(self.root)
        return errors

    def read_eval_manifest(self) -> dict[str, object]:
        return json.loads((self.root / "evals/manifest.json").read_text(encoding="utf-8"))

    def write_eval_manifest(self, manifest: dict[str, object]) -> None:
        (self.root / "evals/manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def eval_case(self, manifest: dict[str, object], case_id: str) -> dict[str, object]:
        cases = manifest["cases"]
        self.assertIsInstance(cases, list)
        for case in cases:
            if isinstance(case, dict) and case.get("id") == case_id:
                return case
        self.fail(f"missing eval fixture {case_id}")

    def test_current_repository_tree_passes(self) -> None:
        errors, skills = check_repository.inspect_tree(REPOSITORY_ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(set(skills), set(check_repository.EXPECTED_SKILLS))

    def test_clean_fixture_passes(self) -> None:
        self.assertEqual(self.inspect_fixture(), [])

    def test_missing_skill_fails_inventory_and_validator_wiring(self) -> None:
        shutil.rmtree(self.root / "skills/reverse-lamport")
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("skill inventory must contain exactly the three Lamport Proof skills", errors)
        self.assertIn("reverse-lamport", errors)

    def test_extra_skill_fails_inventory(self) -> None:
        shutil.copytree(
            self.root / "skills/forward-lamport",
            self.root / "skills/extra-proof-audit",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("skill inventory must contain exactly the three Lamport Proof skills", errors)
        self.assertIn("extra-proof-audit", errors)

    def test_duplicate_manifest_key_fails(self) -> None:
        manifest = self.root / ".codex-plugin/plugin.json"
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(
            text.replace(
                '"name": "lamport-proof",',
                '"name": "lamport-proof",\n  "name": "duplicate",',
                1,
            ),
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("duplicate JSON key 'name'", errors)

    def test_legacy_package_name_fails(self) -> None:
        manifest_path = self.root / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["name"] = "lamport-proof-toolkit"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("manifest name must be 'lamport-proof'", errors)

    def test_manifest_version_and_repository_are_enforced(self) -> None:
        manifest_path = self.root / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = "0.1.0"
        manifest["repository"] = "https://example.invalid/legacy"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("manifest version must be '0.2.0'", errors)
        self.assertIn(
            "manifest repository must be 'https://github.com/WWresearch/lamport-proof'",
            errors,
        )

    def test_required_public_docs_evals_and_staging_script_are_enforced(self) -> None:
        for relative in (
            ".github/ISSUE_TEMPLATE/bug.yml",
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "evals/README.md",
            "scripts/stage_isolated_skills.py",
        ):
            (self.root / relative).unlink()
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("missing required file .github/ISSUE_TEMPLATE/bug.yml", errors)
        self.assertIn("missing required file CODE_OF_CONDUCT.md", errors)
        self.assertIn("missing required file CONTRIBUTING.md", errors)
        self.assertIn("missing required file SECURITY.md", errors)
        self.assertIn("missing required file evals/README.md", errors)
        self.assertIn("missing required file scripts/stage_isolated_skills.py", errors)

    def test_exact_public_description_is_enforced_across_surfaces(self) -> None:
        manifest_path = self.root / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["description"] = "A vague proof toolkit."
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        readme = self.root / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                check_repository.EXPECTED_PUBLIC_DESCRIPTION,
                "A vague proof toolkit.",
                1,
            ),
            encoding="utf-8",
        )

        citation = self.root / "CITATION.cff"
        citation.write_text(
            citation.read_text(encoding="utf-8").replace(
                check_repository.EXPECTED_PUBLIC_DESCRIPTION,
                "A vague proof toolkit.",
                1,
            ),
            encoding="utf-8",
        )

        errors = "\n".join(self.inspect_fixture())
        self.assertIn("manifest description must match the exact public description", errors)
        self.assertIn(
            "README.md must present the exact public description in its introduction",
            errors,
        )
        self.assertIn("CITATION.cff abstract must match the exact public description", errors)

    def test_code_of_conduct_links_are_enforced(self) -> None:
        for filename in ("README.md", "CONTRIBUTING.md"):
            path = self.root / filename
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    check_repository.EXPECTED_CODE_OF_CONDUCT_LINK,
                    "Code of Conduct",
                    1,
                ),
                encoding="utf-8",
            )

        errors = "\n".join(self.inspect_fixture())
        self.assertIn("README.md must link to CODE_OF_CONDUCT.md", errors)
        self.assertIn("CONTRIBUTING.md must link to CODE_OF_CONDUCT.md", errors)

    def test_code_of_conduct_identity_and_contact_are_enforced(self) -> None:
        conduct = self.root / "CODE_OF_CONDUCT.md"
        conduct.write_text(
            conduct.read_text(encoding="utf-8")
            .replace(check_repository.EXPECTED_CONTRIBUTOR_COVENANT_URL, "https://example.invalid")
            .replace(check_repository.EXPECTED_CONTACT, "[INSERT CONTACT METHOD]"),
            encoding="utf-8",
        )

        errors = "\n".join(self.inspect_fixture())
        self.assertIn("CODE_OF_CONDUCT.md must identify Contributor Covenant 2.1", errors)
        self.assertIn("CODE_OF_CONDUCT.md must provide the project reporting contact", errors)
        self.assertIn("CODE_OF_CONDUCT.md contains an unresolved reporting placeholder", errors)

    def test_missing_openai_agent_fails(self) -> None:
        (self.root / "skills/forward-lamport/agents/openai.yaml").unlink()
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("forward-lamport is missing agents/openai.yaml", errors)

    def test_cross_skill_contract_invariants_are_enforced(self) -> None:
        convert = self.root / "skills/convert-lamport/SKILL.md"
        convert.write_text(
            convert.read_text(encoding="utf-8").replace(
                "Structural scaffolding must itself be a legal Lamport hierarchy",
                "Structural scaffolding should be readable",
                1,
            ),
            encoding="utf-8",
        )
        reverse = self.root / "skills/reverse-lamport/SKILL.md"
        reverse.write_text(
            reverse.read_text(encoding="utf-8").replace(
                "Unavailability alone is not `missing`",
                "Unavailable support may be missing",
                1,
            ),
            encoding="utf-8",
        )
        forward = self.root / "skills/forward-lamport/SKILL.md"
        forward.write_text(
            forward.read_text(encoding="utf-8").replace(
                "exact meta-obligation",
                "generic external obligation",
            ),
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("convert-lamport must preserve contract invariant", errors)
        self.assertIn("reverse-lamport must preserve contract invariant", errors)
        self.assertIn("forward-lamport must preserve contract invariant", errors)

    def test_converter_mapping_boundary_is_enforced(self) -> None:
        convert = self.root / "skills/convert-lamport/SKILL.md"
        convert.write_text(
            convert.read_text(encoding="utf-8").replace(
                "Do not let `STRUCTURAL` absorb source-content normalization",
                "Classify the resulting content and structural rows",
                1,
            ),
            encoding="utf-8",
        )

        errors = "\n".join(self.inspect_fixture())
        self.assertIn(
            "Do not let `STRUCTURAL` absorb source-content normalization",
            errors,
        )

    def test_converter_no_proof_boundary_is_enforced(self) -> None:
        convert = self.root / "skills/convert-lamport/SKILL.md"
        convert.write_text(
            convert.read_text(encoding="utf-8").replace(
                "`NOT SOURCE-MAPPABLE` is a pre-rendering stop",
                "`NOT SOURCE-MAPPABLE` ends conversion",
                1,
            ),
            encoding="utf-8",
        )

        errors = "\n".join(self.inspect_fixture())
        self.assertIn("`NOT SOURCE-MAPPABLE` is a pre-rendering stop", errors)

    def test_eval_duplicate_case_id_fails(self) -> None:
        manifest = self.read_eval_manifest()
        cases = manifest["cases"]
        self.assertIsInstance(cases, list)
        self.assertIsInstance(cases[0], dict)
        self.assertIsInstance(cases[1], dict)
        cases[1]["id"] = cases[0]["id"]
        self.write_eval_manifest(manifest)
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("duplicate eval case id 'convert-forward-valid-export'", errors)

    def test_eval_skill_order_and_unknown_legacy_skill_fail(self) -> None:
        manifest = self.read_eval_manifest()
        case = self.eval_case(manifest, "combined-unjustified-pick")
        case["skills"] = ["reverse-lamport", "audit-lamport-proof", "convert-lamport"]
        self.write_eval_manifest(manifest)
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("skills contains unknown skills: ['audit-lamport-proof']", errors)
        self.assertIn("skills must follow convert, forward, reverse order", errors)

    def test_eval_prompt_traversal_fails(self) -> None:
        manifest = self.read_eval_manifest()
        case = self.eval_case(manifest, "forward-private-substep")
        case["prompt"] = "../README.md"
        self.write_eval_manifest(manifest)
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("prompt must be 'cases/forward-private-substep.md'", errors)
        self.assertIn("prompt escapes evals/cases", errors)

    def test_eval_register_prefix_must_match_support_status(self) -> None:
        manifest = self.read_eval_manifest()
        case = self.eval_case(manifest, "convert-forward-unavailable-lemma")
        expected = case["expected"]
        self.assertIsInstance(expected, dict)
        conversion = expected["conversion"]
        self.assertIsInstance(conversion, dict)
        conversion["register_ids"] = ["GAP-001"]
        self.write_eval_manifest(manifest)
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("register id 'GAP-001' does not match its support status", errors)
        self.assertIn("support status 'EXTERNAL UNAVAILABLE' requires a EXT-nnn id", errors)

    def test_not_source_mappable_eval_cannot_claim_rendering(self) -> None:
        manifest = self.read_eval_manifest()
        case = self.eval_case(manifest, "convert-no-proof")
        expected = case["expected"]
        self.assertIsInstance(expected, dict)
        conversion = expected["conversion"]
        self.assertIsInstance(conversion, dict)
        conversion["mapping_kinds"] = ["DIRECT"]
        self.write_eval_manifest(manifest)
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("NOT SOURCE-MAPPABLE expectations must not claim a rendering", errors)

    def test_eval_outcome_taxonomies_are_enforced(self) -> None:
        manifest = self.read_eval_manifest()
        no_proof = self.eval_case(manifest, "convert-no-proof")
        no_proof_expected = no_proof["expected"]
        self.assertIsInstance(no_proof_expected, dict)
        no_proof_conversion = no_proof_expected["conversion"]
        self.assertIsInstance(no_proof_conversion, dict)
        no_proof_conversion["status"] = "UNSUPPORTED"

        forward = self.eval_case(manifest, "forward-private-substep")
        forward_expected = forward["expected"]
        self.assertIsInstance(forward_expected, dict)
        forward_expected["forward"] = "FOLLOWS"

        reverse = self.eval_case(manifest, "reverse-valid-even-square")
        reverse_expected = reverse["expected"]
        self.assertIsInstance(reverse_expected, dict)
        reverse_expected["reverse"] = "PASS"
        self.write_eval_manifest(manifest)

        errors = "\n".join(self.inspect_fixture())
        self.assertIn("has an invalid conversion status", errors)
        self.assertIn("has an invalid forward verdict", errors)
        self.assertIn("has an invalid reverse verdict", errors)

    def test_eval_expected_axes_must_match_invoked_skills(self) -> None:
        manifest = self.read_eval_manifest()
        case = self.eval_case(manifest, "forward-private-substep")
        expected = case["expected"]
        self.assertIsInstance(expected, dict)
        expected["reverse"] = "FOLLOWS"
        self.write_eval_manifest(manifest)

        errors = "\n".join(self.inspect_fixture())
        self.assertIn("expected axes must be ['forward']", errors)

    def test_eval_required_status_coverage_is_enforced(self) -> None:
        manifest = self.read_eval_manifest()
        case = self.eval_case(manifest, "convert-no-proof")
        expected = case["expected"]
        self.assertIsInstance(expected, dict)
        conversion = expected["conversion"]
        self.assertIsInstance(conversion, dict)
        conversion["status"] = "SOURCE-MAPPED"
        self.write_eval_manifest(manifest)

        errors = "\n".join(self.inspect_fixture())
        self.assertIn("evals must cover all conversion statuses", errors)

    def test_eval_prompt_must_not_disclose_expected_outcome(self) -> None:
        prompt = self.root / "evals/cases/forward-private-substep.md"
        prompt.write_text(
            prompt.read_text(encoding="utf-8") + "\nExpected verdict: FAIL\n",
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("prompt discloses expected outcome 'FAIL'", errors)

    def test_eval_title_must_not_disclose_diagnosis(self) -> None:
        prompt = self.root / "evals/cases/forward-private-substep.md"
        text = prompt.read_text(encoding="utf-8")
        prompt.write_text(
            text.replace(
                "# Audit a hierarchical implication proof",
                "# Audit an illegal private-substep citation",
                1,
            ),
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("prompt title discloses an outcome-loaded diagnosis", errors)

    def test_orphan_eval_prompt_fails(self) -> None:
        (self.root / "evals/cases/orphan.md").write_text(
            "Use $forward-lamport on this orphan fixture.\n",
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("orphan eval prompt files: ['cases/orphan.md']", errors)

    def test_local_path_and_generated_residue_fail(self) -> None:
        local_paths = (
            "/" + "home/alice",
            "/" + "Users/alice",
            "C:" + "\\Users\\Alice",
            "\\\\wsl.localhost\\Ubuntu\\home\\alice",
            ".codex" + "\\plugins\\cache",
        )
        (self.root / "notes.md").write_text(
            "Do not publish " + "\n".join(local_paths) + "\n",
            encoding="utf-8",
        )
        residue = self.root / "__pycache__"
        residue.mkdir()
        (residue / "state.pyc").write_bytes(b"compiled")
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("forbidden POSIX user-home path", errors)
        self.assertIn("forbidden Windows user-home path", errors)
        self.assertIn("forbidden WSL user-home path", errors)
        self.assertIn("forbidden Codex cache path", errors)
        self.assertIn("forbidden path component", errors)
        self.assertIn("forbidden generated or credential artifact", errors)

    def test_credential_names_and_unclassified_binary_fail(self) -> None:
        (self.root / ".envrc").write_text("TOKEN=redacted\n", encoding="utf-8")
        (self.root / "credentials").write_text("redacted\n", encoding="utf-8")
        (self.root / "ID_RSA").write_text("redacted\n", encoding="utf-8")
        (self.root / "payload.bin").write_bytes(b"binary\xff")
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("forbidden file name: .envrc", errors)
        self.assertIn("forbidden file name: ID_RSA", errors)
        self.assertIn("forbidden credential file name: credentials", errors)
        self.assertIn("unclassified binary or non-UTF-8 file is not allowed: payload.bin", errors)

    def test_future_text_extensions_are_scanned(self) -> None:
        (self.root / "configuration.toml").write_text(
            'workspace = "' + "/" + 'home/alice"\n',
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("forbidden POSIX user-home path", errors)

    def test_marketplace_directory_is_rejected(self) -> None:
        marketplace = self.root / (".agents" + "/plugins")
        marketplace.mkdir(parents=True)
        (marketplace / "catalog.json").write_text("{}\n", encoding="utf-8")
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("personal marketplace path is not allowed", errors)

    def test_symlink_fails(self) -> None:
        (self.root / "README.link").symlink_to(self.root / "README.md")
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("symlink is not allowed: README.link", errors)

    def test_future_unittest_failure_is_observed(self) -> None:
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_future.py").write_text(
            "import unittest\n\n"
            "class FutureTest(unittest.TestCase):\n"
            "    def test_failure(self):\n"
            "        self.fail('intentional fixture failure')\n",
            encoding="utf-8",
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            passed = check_repository.run_regression_tests(self.root)
        self.assertFalse(passed)
        self.assertIn("FAIL repository tests", output.getvalue())

    def test_empty_test_directory_fails(self) -> None:
        (self.root / "tests").mkdir()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            passed = check_repository.run_regression_tests(self.root)
        self.assertFalse(passed)
        self.assertIn("No test_*.py files were discovered", output.getvalue())

    def test_nested_nonpackage_test_fails(self) -> None:
        nested = self.root / "tests/nested"
        nested.mkdir(parents=True)
        (nested / "test_hidden.py").write_text(
            "import unittest\n\n"
            "class HiddenTest(unittest.TestCase):\n"
            "    def test_hidden_failure(self):\n"
            "        self.fail('must not be skipped')\n",
            encoding="utf-8",
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            passed = check_repository.run_regression_tests(self.root)
        self.assertFalse(passed)
        self.assertIn("missing __init__.py", output.getvalue())

    def test_nonimportable_test_filename_fails(self) -> None:
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_bad-name.py").write_text(
            "import unittest\n\n"
            "class HiddenTest(unittest.TestCase):\n"
            "    def test_hidden_failure(self):\n"
            "        self.fail('must not be skipped')\n",
            encoding="utf-8",
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            passed = check_repository.run_regression_tests(self.root)
        self.assertFalse(passed)
        self.assertIn("is not importable by unittest", output.getvalue())

    def test_test_mutation_is_observed(self) -> None:
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_mutation.py").write_text(
            "import pathlib\n"
            "import unittest\n\n"
            "class MutationTest(unittest.TestCase):\n"
            "    def test_mutates_repository(self):\n"
            "        root = pathlib.Path(__file__).resolve().parents[1]\n"
            "        (root / 'test-residue.txt').write_text('residue', encoding='utf-8')\n",
            encoding="utf-8",
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            passed = check_repository.run_regression_tests(self.root)
        self.assertFalse(passed)
        self.assertIn("FAIL repository tests mutated the repository", output.getvalue())
        self.assertIn("added test-residue.txt", output.getvalue())

    def test_main_runs_plugin_and_exactly_three_skill_validators(self) -> None:
        plugin_validator = self.root / "plugin-validator.py"
        skill_validator = self.root / "skill-validator.py"
        plugin_validator.write_text("# fixture\n", encoding="utf-8")
        skill_validator.write_text("# fixture\n", encoding="utf-8")
        calls: list[str] = []

        def record_call(label: str, *args: object, **kwargs: object) -> bool:
            calls.append(label)
            return True

        with (
            mock.patch.object(
                check_repository,
                "validator_paths",
                return_value=(plugin_validator, skill_validator),
            ),
            mock.patch.object(check_repository, "run_command", side_effect=record_call),
            mock.patch.object(check_repository, "run_regression_tests", return_value=True) as tests,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            exit_code = check_repository.main([])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            calls,
            [
                "plugin manifest",
                "skill convert-lamport",
                "skill forward-lamport",
                "skill reverse-lamport",
            ],
        )
        tests.assert_called_once_with(check_repository.DEFAULT_ROOT)

    def test_main_propagates_validator_failure(self) -> None:
        plugin_validator = self.root / "plugin-validator.py"
        skill_validator = self.root / "skill-validator.py"
        plugin_validator.write_text("# fixture\n", encoding="utf-8")
        skill_validator.write_text("# fixture\n", encoding="utf-8")
        with (
            mock.patch.object(
                check_repository,
                "validator_paths",
                return_value=(plugin_validator, skill_validator),
            ),
            mock.patch.object(
                check_repository,
                "run_command",
                side_effect=[False, True, True, True],
            ),
            mock.patch.object(check_repository, "run_regression_tests", return_value=True),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            exit_code = check_repository.main([])
        self.assertEqual(exit_code, 1)

    def test_main_observes_validator_tree_mutation(self) -> None:
        plugin_validator = self.root / "plugin-validator.py"
        skill_validator = self.root / "skill-validator.py"
        plugin_validator.write_text("# fixture\n", encoding="utf-8")
        skill_validator.write_text("# fixture\n", encoding="utf-8")

        def mutate_on_first_call(*args: object, **kwargs: object) -> bool:
            if not (self.root / "validator-residue.txt").exists():
                (self.root / "validator-residue.txt").write_text("residue\n", encoding="utf-8")
            return True

        output = io.StringIO()
        with (
            mock.patch.object(check_repository, "DEFAULT_ROOT", self.root),
            mock.patch.object(
                check_repository,
                "validator_paths",
                return_value=(plugin_validator, skill_validator),
            ),
            mock.patch.object(check_repository, "run_command", side_effect=mutate_on_first_call),
            mock.patch.object(check_repository, "run_regression_tests", return_value=True),
            contextlib.redirect_stdout(output),
        ):
            exit_code = check_repository.main([])

        self.assertEqual(exit_code, 1)
        self.assertIn("FAIL validation commands mutated the repository", output.getvalue())

    def test_main_skip_tests_is_explicit(self) -> None:
        plugin_validator = self.root / "plugin-validator.py"
        skill_validator = self.root / "skill-validator.py"
        plugin_validator.write_text("# fixture\n", encoding="utf-8")
        skill_validator.write_text("# fixture\n", encoding="utf-8")
        output = io.StringIO()
        with (
            mock.patch.object(
                check_repository,
                "validator_paths",
                return_value=(plugin_validator, skill_validator),
            ),
            mock.patch.object(check_repository, "run_command", return_value=True),
            mock.patch.object(check_repository, "run_regression_tests") as tests,
            contextlib.redirect_stdout(output),
        ):
            exit_code = check_repository.main(["--skip-tests"])
        self.assertEqual(exit_code, 0)
        tests.assert_not_called()
        self.assertIn("SKIP repository tests (--skip-tests)", output.getvalue())

    def test_main_skip_codex_validators_is_explicit_and_keeps_tests(self) -> None:
        missing = self.root / "missing.py"
        output = io.StringIO()
        with (
            mock.patch.object(check_repository, "DEFAULT_ROOT", self.root),
            mock.patch.object(
                check_repository,
                "validator_paths",
                return_value=(missing, missing),
            ),
            mock.patch.object(check_repository, "run_command") as command,
            mock.patch.object(
                check_repository,
                "run_regression_tests",
                return_value=True,
            ) as tests,
            contextlib.redirect_stdout(output),
        ):
            exit_code = check_repository.main(["--skip-codex-validators"])

        self.assertEqual(exit_code, 0)
        command.assert_not_called()
        tests.assert_called_once_with(self.root)
        self.assertIn(
            "SKIP Codex plugin/skill validators (--skip-codex-validators)",
            output.getvalue(),
        )

    def test_main_returns_two_when_validators_are_missing(self) -> None:
        missing = self.root / "missing.py"
        with (
            mock.patch.object(check_repository, "validator_paths", return_value=(missing, missing)),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            exit_code = check_repository.main([])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
