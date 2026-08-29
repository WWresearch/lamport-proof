from __future__ import annotations

import contextlib
import io
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
        self.root = Path(self.temporary_directory.name) / "lamport-proof-toolkit"
        self.root.mkdir()
        for directory in (".codex-plugin", "skills"):
            shutil.copytree(REPOSITORY_ROOT / directory, self.root / directory)
        (self.root / "scripts").mkdir()
        shutil.copy2(
            REPOSITORY_ROOT / "scripts/check_repository.py",
            self.root / "scripts/check_repository.py",
        )
        for filename in ("LICENSE", "PROVENANCE.md", "README.md"):
            shutil.copy2(REPOSITORY_ROOT / filename, self.root / filename)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def inspect_fixture(self) -> list[str]:
        errors, _ = check_repository.inspect_tree(self.root)
        return errors

    def test_current_repository_tree_passes(self) -> None:
        errors, skills = check_repository.inspect_tree(REPOSITORY_ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(set(skills), set(check_repository.EXPECTED_SKILLS))

    def test_clean_fixture_passes(self) -> None:
        self.assertEqual(self.inspect_fixture(), [])

    def test_missing_skill_fails_inventory_and_validator_wiring(self) -> None:
        shutil.rmtree(self.root / "skills/reverse-lamport")
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("skill inventory must contain exactly both toolkit skills", errors)
        self.assertIn("reverse-lamport", errors)

    def test_extra_skill_fails_inventory(self) -> None:
        shutil.copytree(
            self.root / "skills/audit-lamport-proof",
            self.root / "skills/extra-proof-audit",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("skill inventory must contain exactly both toolkit skills", errors)
        self.assertIn("extra-proof-audit", errors)

    def test_duplicate_manifest_key_fails(self) -> None:
        manifest = self.root / ".codex-plugin/plugin.json"
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(
            text.replace(
                '"name": "lamport-proof-toolkit",',
                '"name": "lamport-proof-toolkit",\n  "name": "duplicate",',
                1,
            ),
            encoding="utf-8",
        )
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("duplicate JSON key 'name'", errors)

    def test_missing_openai_agent_fails(self) -> None:
        (self.root / "skills/audit-lamport-proof/agents/openai.yaml").unlink()
        errors = "\n".join(self.inspect_fixture())
        self.assertIn("audit-lamport-proof is missing agents/openai.yaml", errors)

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

    def test_main_runs_plugin_and_exactly_both_skill_validators(self) -> None:
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
                "skill audit-lamport-proof",
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
            mock.patch.object(check_repository, "run_command", side_effect=[False, True, True]),
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
