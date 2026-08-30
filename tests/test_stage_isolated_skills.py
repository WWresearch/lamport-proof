from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import stage_isolated_skills


class IsolatedSkillStagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temporary_root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def tree_snapshot(root: Path) -> dict[str, tuple[str, bytes | str | None]]:
        if not root.exists():
            return {}
        snapshot: dict[str, tuple[str, bytes | str | None]] = {}
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                snapshot[relative] = ("symlink", os.readlink(path))
            elif path.is_dir():
                snapshot[relative] = ("directory", None)
            else:
                snapshot[relative] = ("file", path.read_bytes())
        return snapshot

    def test_stages_exactly_three_complete_skill_copies(self) -> None:
        codex_home = self.temporary_root / "isolated-codex"

        installed = stage_isolated_skills.stage_skills(codex_home)

        skills_root = codex_home / "skills"
        self.assertEqual(
            installed,
            [skills_root / name for name in stage_isolated_skills.SKILL_NAMES],
        )
        self.assertEqual(
            {path.name for path in skills_root.iterdir()},
            set(stage_isolated_skills.SKILL_NAMES),
        )
        for name in stage_isolated_skills.SKILL_NAMES:
            source = REPOSITORY_ROOT / "skills" / name
            destination = skills_root / name
            self.assertEqual(
                self.tree_snapshot(destination),
                self.tree_snapshot(source),
                msg=f"staged skill differs from source: {name}",
            )
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_rejects_relative_home(self) -> None:
        with self.assertRaisesRegex(
            stage_isolated_skills.StagingError,
            "must be an absolute path",
        ):
            stage_isolated_skills.stage_skills(Path("relative-codex-home"))

    def test_rejects_default_global_home(self) -> None:
        default_home = Path.home() / ".codex"

        with self.assertRaisesRegex(
            stage_isolated_skills.StagingError,
            "active or default global Codex home",
        ):
            stage_isolated_skills.stage_skills(default_home)

    def test_rejects_configured_active_home(self) -> None:
        active_home = self.temporary_root / "configured-codex-home"

        with (
            mock.patch.dict(os.environ, {"CODEX_HOME": str(active_home)}),
            self.assertRaisesRegex(
                stage_isolated_skills.StagingError,
                "active or default global Codex home",
            ),
        ):
            stage_isolated_skills.stage_skills(active_home)

        self.assertFalse(active_home.exists())

    def test_rejects_destination_inside_repository(self) -> None:
        repository = self.temporary_root / "repository"
        repository.mkdir()
        contained_home = repository / "isolated-codex-home"

        with (
            mock.patch.object(stage_isolated_skills, "REPOSITORY_ROOT", repository),
            self.assertRaisesRegex(
                stage_isolated_skills.StagingError,
                "must be outside the repository and must not contain it",
            ),
        ):
            stage_isolated_skills.stage_skills(contained_home)

        self.assertFalse(contained_home.exists())

    def test_rejects_destination_that_contains_repository(self) -> None:
        containing_home = self.temporary_root / "containing-codex-home"
        repository = containing_home / "checkout"
        repository.mkdir(parents=True)

        with (
            mock.patch.object(stage_isolated_skills, "REPOSITORY_ROOT", repository),
            self.assertRaisesRegex(
                stage_isolated_skills.StagingError,
                "must be outside the repository and must not contain it",
            ),
        ):
            stage_isolated_skills.stage_skills(containing_home)

        self.assertFalse((containing_home / "skills").exists())

    def test_rejects_symlinked_destination_component(self) -> None:
        real_parent = self.temporary_root / "real-parent"
        real_parent.mkdir()
        linked_parent = self.temporary_root / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)

        with self.assertRaisesRegex(
            stage_isolated_skills.StagingError,
            "symlinked destination component is not allowed",
        ):
            stage_isolated_skills.stage_skills(linked_parent / "isolated-codex-home")

        self.assertEqual(list(real_parent.iterdir()), [])

    def test_preexisting_toolkit_skill_prevents_every_write(self) -> None:
        codex_home = self.temporary_root / "isolated-codex"
        existing = codex_home / "skills" / "forward-lamport"
        existing.mkdir(parents=True)
        (existing / "sentinel.txt").write_text("keep\n", encoding="utf-8")
        before = self.tree_snapshot(codex_home)

        with self.assertRaisesRegex(
            stage_isolated_skills.StagingError,
            "destination skill already exists",
        ):
            stage_isolated_skills.stage_skills(codex_home)

        self.assertEqual(self.tree_snapshot(codex_home), before)
        self.assertFalse((codex_home / "skills" / "convert-lamport").exists())
        self.assertFalse((codex_home / "skills" / "reverse-lamport").exists())
        self.assertEqual(
            list(self.temporary_root.glob(".lamport-proof-stage-*")),
            [],
        )

    def test_mid_install_failure_restores_existing_destination(self) -> None:
        codex_home = self.temporary_root / "isolated-codex"
        unrelated_skill = codex_home / "skills" / "unrelated-skill"
        unrelated_skill.mkdir(parents=True)
        (unrelated_skill / "SKILL.md").write_text("unrelated\n", encoding="utf-8")
        before = self.tree_snapshot(codex_home)
        real_replace = os.replace
        replace_calls = 0

        def fail_on_second_replace(source: os.PathLike[str], target: os.PathLike[str]) -> None:
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls == 2:
                raise OSError("simulated second-skill install failure")
            real_replace(source, target)

        with (
            mock.patch.object(
                stage_isolated_skills.os,
                "replace",
                side_effect=fail_on_second_replace,
            ),
            self.assertRaisesRegex(OSError, "simulated second-skill install failure"),
        ):
            stage_isolated_skills.stage_skills(codex_home)

        self.assertEqual(replace_calls, 2)
        self.assertEqual(self.tree_snapshot(codex_home), before)
        self.assertEqual(
            list(self.temporary_root.glob(".lamport-proof-stage-*")),
            [],
        )


if __name__ == "__main__":
    unittest.main()
