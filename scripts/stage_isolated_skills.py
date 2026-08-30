#!/usr/bin/env python3
"""Stage Lamport Proof skills into an isolated Codex home."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import tempfile
from typing import Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = ("convert-lamport", "forward-lamport", "reverse-lamport")


class StagingError(Exception):
    """Raised when an isolated staging request is unsafe or incomplete."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy all Lamport Proof skills into a non-global Codex home."
    )
    parser.add_argument(
        "--codex-home",
        required=True,
        type=Path,
        help="Absolute path to the isolated Codex home.",
    )
    return parser.parse_args(argv)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.exists() and current.is_symlink():
            raise StagingError(f"symlinked destination component is not allowed: {current}")


def validate_source(skill_path: Path) -> None:
    if not skill_path.is_dir() or not (skill_path / "SKILL.md").is_file():
        raise StagingError(f"invalid source skill: {skill_path}")
    for path in skill_path.rglob("*"):
        if path.is_symlink():
            raise StagingError(f"source skill contains a symlink: {path}")


def validate_destination(raw_home: Path) -> Path:
    expanded = raw_home.expanduser()
    if not expanded.is_absolute():
        raise StagingError("--codex-home must be an absolute path")

    reject_symlink_components(expanded)
    destination = expanded.resolve(strict=False)
    repository = REPOSITORY_ROOT.resolve()
    if is_within(destination, repository) or is_within(repository, destination):
        raise StagingError(
            "the isolated Codex home must be outside the repository and must not contain it"
        )

    configured_home = Path(
        os.environ.get("CODEX_HOME", Path.home() / ".codex")
    ).expanduser().resolve(strict=False)
    default_home = (Path.home() / ".codex").resolve(strict=False)
    if destination in {configured_home, default_home}:
        raise StagingError("refusing to stage into the active or default global Codex home")

    skills_root = destination / "skills"
    if skills_root.exists() and skills_root.is_symlink():
        raise StagingError("the destination skills directory must not be a symlink")
    existing = [skills_root / name for name in SKILL_NAMES if (skills_root / name).exists()]
    if existing:
        raise StagingError(
            "destination skill already exists: " + ", ".join(str(path) for path in existing)
        )
    return destination


def stage_skills(codex_home: Path) -> list[Path]:
    destination = validate_destination(codex_home)
    sources = [REPOSITORY_ROOT / "skills" / name for name in SKILL_NAMES]
    for source in sources:
        validate_source(source)

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=".lamport-proof-stage-", dir=destination.parent)
    )
    staged_root = temporary / "skills"
    installed: list[Path] = []
    created_skills_root = False
    try:
        staged_root.mkdir()
        for source, name in zip(sources, SKILL_NAMES, strict=True):
            shutil.copytree(source, staged_root / name)

        skills_root = destination / "skills"
        destination.mkdir(parents=True, exist_ok=True)
        if not skills_root.exists():
            skills_root.mkdir()
            created_skills_root = True
        for name in SKILL_NAMES:
            target = skills_root / name
            if target.exists():
                raise StagingError(f"destination skill appeared during staging: {target}")
            os.replace(staged_root / name, target)
            installed.append(target)
    except Exception:
        for target in reversed(installed):
            shutil.rmtree(target, ignore_errors=True)
        skills_root = destination / "skills"
        if created_skills_root and skills_root.is_dir() and not any(skills_root.iterdir()):
            skills_root.rmdir()
        raise
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
    return installed


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        installed = stage_skills(args.codex_home)
    except (OSError, StagingError) as error:
        print(f"Error: {error}")
        return 1

    for path in installed:
        print(f"Staged {path.name} at {path}")
    home = args.codex_home.expanduser().resolve(strict=False)
    print("Start an isolated session with:")
    print(f"  CODEX_HOME={shlex.quote(str(home))} codex")
    print("Authentication and user configuration were not copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
