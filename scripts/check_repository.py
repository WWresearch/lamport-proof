#!/usr/bin/env python3
"""Validate the standalone Lamport Proof Toolkit repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Callable, Pattern, Sequence
import unicodedata


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PLUGIN_NAME = "lamport-proof-toolkit"
EXPECTED_AUTHOR = "Wojciech Aleksander Wołoszyn (WWresearch)"
EXPECTED_DEVELOPER = "WWresearch"
EXPECTED_WEBSITE = "https://www.wwresearch.org/"
EXPECTED_SKILLS = frozenset({"audit-lamport-proof", "reverse-lamport"})
REQUIRED_ROOT_FILES = (
    ".codex-plugin/plugin.json",
    "LICENSE",
    "PROVENANCE.md",
    "README.md",
    "scripts/check_repository.py",
)
ALLOWED_BINARY_SUFFIXES = frozenset({".gif", ".jpeg", ".jpg", ".png", ".webp"})
EXPECTED_LICENSE_SHA256 = "66ad5029d3b06e5983de8cf062373c123b47e4ad5b8dddf3edc949199d1f2e01"
EXPECTED_PREDECESSOR_COMMIT = "c6ff5a822bfa4e0a6ef9decf91548173e4fb108c"
FORBIDDEN_COMPONENTS = frozenset(
    {
        ".ds_store",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "thumbs.db",
    }
)
FORBIDDEN_FILENAMES = frozenset(
    {
        ".coverage",
        ".env",
        ".env.local",
        "id_ed25519",
        "id_rsa",
        "marketplace.json",
    }
)
FORBIDDEN_SUFFIXES = (
    ".bak",
    ".key",
    ".orig",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
    ".pyo",
    ".swp",
    ".swo",
    ".tmp",
    ".rej",
    ".Zone.Identifier",
    "~",
)
FORBIDDEN_TEXT_MARKERS = (
    "[" + "TODO:",
    "sandbox:" + "/mnt/data",
    chr(0),
    chr(0xE200),
    chr(0xFEFF),
)
SENSITIVE_TEXT_PATTERNS: tuple[tuple[str, Pattern[str]], ...] = (
    (
        "POSIX user-home path",
        re.compile(
            r"(?<![A-Za-z0-9])/(?:home|Users)/[A-Za-z0-9._-]+"
            r"(?=$|[/\s`'\"),.;:])"
        ),
    ),
    (
        "Windows user-home path",
        re.compile(
            r"(?i)(?<![A-Za-z0-9])[A-Z]:[\\/]+Users[\\/]+"
            r"[^\\/\s`'\"),.;:]+(?=$|[\\/\s`'\"),.;:])"
        ),
    ),
    (
        "WSL user-home path",
        re.compile(
            r"(?i)(?<![A-Za-z0-9])\\\\wsl(?:\.localhost|\$)\\[^\\\s]+"
            r"\\home\\[^\\/\s`'\"),.;:]+(?=$|[\\/\s`'\"),.;:])"
        ),
    ),
    ("local file URI", re.compile(re.escape("file" + "://"), re.IGNORECASE)),
    ("Codex cache path", re.compile(r"\.codex[\\/]+plugins[\\/]+cache", re.IGNORECASE)),
    ("Claude cache path", re.compile(r"\.claude[\\/]+plugins[\\/]+cache", re.IGNORECASE)),
    ("personal marketplace path", re.compile(r"\.agents[\\/]+plugins", re.IGNORECASE)),
    ("private-key material", re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")),
    ("AWS access-key identifier", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the standalone Lamport Proof Toolkit repository."
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Run structural and Codex validators without repository regression tests.",
    )
    return parser.parse_args(argv)


def validator_paths() -> tuple[Path, Path]:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    return (
        codex_home / "skills/.system/plugin-creator/scripts/validate_plugin.py",
        codex_home / "skills/.system/skill-creator/scripts/quick_validate.py",
    )


def run_command(label: str, command: Sequence[str], cwd: Path, *, timeout: int = 300) -> bool:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            list(command),
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL {label}\n{error}")
        return False

    stream = (result.stdout + result.stderr).rstrip()
    if result.returncode:
        print(f"FAIL {label}")
        if stream:
            print(stream)
        return False

    print(f"PASS {label}")
    return True


def run_command_requiring_output(
    label: str,
    command: Sequence[str],
    cwd: Path,
    required_output: Pattern[str],
    *,
    timeout: int = 300,
) -> bool:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            list(command),
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL {label}\n{error}")
        return False

    stream = (result.stdout + result.stderr).rstrip()
    if result.returncode or required_output.search(stream) is None:
        print(f"FAIL {label}")
        if stream:
            print(stream)
        elif not result.returncode:
            print("Required success evidence was absent from command output.")
        return False

    print(f"PASS {label}")
    return True


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key {key!r}")
        payload[key] = value
    return payload


def load_manifest(root: Path, errors: list[str]) -> dict[str, object] | None:
    manifest_path = root / ".codex-plugin/plugin.json"
    try:
        payload = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_json_keys,
        )
    except FileNotFoundError:
        errors.append("missing .codex-plugin/plugin.json")
        return None
    except OSError as error:
        errors.append(f"cannot read .codex-plugin/plugin.json: {error}")
        return None
    except json.JSONDecodeError as error:
        errors.append(f"invalid JSON in .codex-plugin/plugin.json: {error}")
        return None
    except ValueError as error:
        errors.append(f"invalid JSON in .codex-plugin/plugin.json: {error}")
        return None

    if not isinstance(payload, dict):
        errors.append(".codex-plugin/plugin.json must contain a JSON object")
        return None
    return payload


def inspect_manifest(root: Path, errors: list[str]) -> None:
    manifest = load_manifest(root, errors)
    if manifest is None:
        return

    if manifest.get("name") != EXPECTED_PLUGIN_NAME:
        errors.append(f"manifest name must be {EXPECTED_PLUGIN_NAME!r}")
    if manifest.get("skills") != "./skills/":
        errors.append("manifest skills path must be './skills/'")
    if manifest.get("license") != "MIT":
        errors.append("manifest license must be 'MIT'")

    author = manifest.get("author")
    if not isinstance(author, dict) or author.get("name") != EXPECTED_AUTHOR:
        errors.append(f"manifest author.name must be {EXPECTED_AUTHOR!r}")
    if not isinstance(author, dict) or author.get("url") != EXPECTED_WEBSITE:
        errors.append(f"manifest author.url must be {EXPECTED_WEBSITE!r}")
    if manifest.get("homepage") != EXPECTED_WEBSITE:
        errors.append(f"manifest homepage must be {EXPECTED_WEBSITE!r}")

    interface = manifest.get("interface")
    if not isinstance(interface, dict) or interface.get("developerName") != EXPECTED_DEVELOPER:
        errors.append(f"manifest interface.developerName must be {EXPECTED_DEVELOPER!r}")
    if not isinstance(interface, dict) or interface.get("websiteURL") != EXPECTED_WEBSITE:
        errors.append(f"manifest interface.websiteURL must be {EXPECTED_WEBSITE!r}")
    prompts = interface.get("defaultPrompt") if isinstance(interface, dict) else None
    if not isinstance(prompts, list) or not all(isinstance(prompt, str) for prompt in prompts):
        errors.append("manifest interface.defaultPrompt must be a list of strings")
    else:
        lowered_prompts = [prompt.casefold() for prompt in prompts]
        if not any("hierarchical" in prompt and "audit" in prompt for prompt in lowered_prompts):
            errors.append("manifest starter prompts must cover the forward hierarchy audit")
        if not any("backward" in prompt or "obligation" in prompt for prompt in lowered_prompts):
            errors.append("manifest starter prompts must cover the reverse obligation audit")
        if not any("both" in prompt for prompt in lowered_prompts):
            errors.append("manifest starter prompts must cover running both audits")


def inspect_required_files(root: Path, errors: list[str]) -> None:
    for relative in REQUIRED_ROOT_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file {relative}")

    license_path = root / "LICENSE"
    if license_path.is_file():
        try:
            license_text = license_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"cannot read LICENSE as UTF-8: {error}")
        else:
            digest = hashlib.sha256(license_text.encode("utf-8")).hexdigest()
            if digest != EXPECTED_LICENSE_SHA256:
                errors.append("LICENSE must match the canonical project MIT license text")

    provenance_path = root / "PROVENANCE.md"
    if provenance_path.is_file():
        try:
            provenance_text = provenance_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"cannot read PROVENANCE.md as UTF-8: {error}")
        else:
            if EXPECTED_PREDECESSOR_COMMIT not in provenance_text:
                errors.append("PROVENANCE.md must identify the predecessor source commit")
            if "`v0.1.0`" not in provenance_text:
                errors.append("PROVENANCE.md must identify the initial standalone tag")


def discover_skill_directories(root: Path, errors: list[str]) -> dict[str, Path]:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        errors.append("missing skills directory")
        return {}

    discovered: dict[str, Path] = {}
    try:
        children = sorted(skills_root.iterdir(), key=lambda path: path.name)
    except OSError as error:
        errors.append(f"cannot list skills directory: {error}")
        return {}

    for child in children:
        if child.is_symlink():
            continue
        if not child.is_dir():
            errors.append(f"unexpected file directly under skills/: {child.name}")
            continue
        if not (child / "SKILL.md").is_file():
            errors.append(f"skill directory {child.name} is missing SKILL.md")
            continue
        discovered[child.name] = child

    names = frozenset(discovered)
    if names != EXPECTED_SKILLS:
        missing = sorted(EXPECTED_SKILLS - names)
        extra = sorted(names - EXPECTED_SKILLS)
        details: list[str] = []
        if missing:
            details.append(f"missing={missing}")
        if extra:
            details.append(f"extra={extra}")
        errors.append("skill inventory must contain exactly both toolkit skills" + (f" ({', '.join(details)})" if details else ""))
    return discovered


def extract_frontmatter(skill_text: str) -> str | None:
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", skill_text, re.DOTALL)
    return match.group(1) if match is not None else None


def inspect_skill_wiring(root: Path, skills: dict[str, Path], errors: list[str]) -> None:
    skill_texts: dict[str, str] = {}
    for directory_name, skill_path in sorted(skills.items()):
        skill_file = skill_path / "SKILL.md"
        try:
            skill_text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"cannot read {skill_file.relative_to(skill_path.parent.parent)}: {error}")
            continue
        skill_texts[directory_name] = skill_text

        frontmatter = extract_frontmatter(skill_text)
        if frontmatter is None:
            errors.append(f"skill {directory_name} is missing valid YAML frontmatter boundaries")
            continue
        frontmatter_names = re.findall(r"^name:\s*([^\n]*)$", frontmatter, re.MULTILINE)
        if len(frontmatter_names) != 1 or frontmatter_names[0].strip() != directory_name:
            errors.append(f"skill {directory_name} frontmatter name must match its directory")
        descriptions = re.findall(r"^description:\s*([^\n]*)$", frontmatter, re.MULTILINE)
        if len(descriptions) != 1 or not descriptions[0].strip():
            errors.append(f"skill {directory_name} must have one nonempty frontmatter description")

        ui_path = skill_path / "agents/openai.yaml"
        if not ui_path.is_file():
            errors.append(f"skill {directory_name} is missing agents/openai.yaml")
            continue
        try:
            ui_text = ui_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"cannot read skill {directory_name} agents/openai.yaml: {error}")
            continue
        default_prompt = re.search(r"^\s*default_prompt:\s*(.*)$", ui_text, re.MULTILINE)
        if default_prompt is None or f"${directory_name}" not in default_prompt.group(1):
            errors.append(f"skill {directory_name} UI prompt must name ${directory_name}")

    forward = skill_texts.get("audit-lamport-proof", "")
    reverse = skill_texts.get("reverse-lamport", "")
    if forward and "$reverse-lamport" not in forward:
        errors.append("audit-lamport-proof must reference $reverse-lamport")
    if reverse and "$audit-lamport-proof" not in reverse:
        errors.append("reverse-lamport must reference $audit-lamport-proof")

    worked_audit = root / "skills/reverse-lamport/references/worked-audit.md"
    if not worked_audit.is_file():
        errors.append("reverse-lamport is missing references/worked-audit.md")


def scan_text(relative_text: str, text: str, record: Callable[[str], None]) -> None:
    for marker in FORBIDDEN_TEXT_MARKERS:
        if marker in text:
            record(f"forbidden workflow marker {marker!r} in {relative_text}")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in SENSITIVE_TEXT_PATTERNS:
            if pattern.search(line):
                record(f"forbidden {label} in {relative_text}:{line_number}")


def inspect_repository_hygiene(root: Path, errors: list[str]) -> None:
    try:
        paths = sorted(root.rglob("*"), key=lambda path: path.as_posix())
    except OSError as error:
        errors.append(f"cannot walk repository: {error}")
        return

    seen_errors: set[str] = set()
    normalized_paths: dict[str, str] = {}
    for path in paths:
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        relative_text = relative.as_posix()

        def record(message: str) -> None:
            if message not in seen_errors:
                seen_errors.add(message)
                errors.append(message)

        if path.is_symlink():
            record(f"symlink is not allowed: {relative_text}")
            continue
        if ".git" in relative.parts:
            record(f"nested Git metadata is not allowed: {relative_text}")
            continue
        if any(ord(character) < 32 for character in relative_text):
            record(f"control character is not allowed in path: {relative_text!r}")
        normalized = unicodedata.normalize("NFC", relative_text).casefold()
        previous = normalized_paths.get(normalized)
        if previous is not None and previous != relative_text:
            record(f"case-fold or Unicode-normalized path collision: {previous} and {relative_text}")
        else:
            normalized_paths[normalized] = relative_text
        if any(component.casefold() in FORBIDDEN_COMPONENTS for component in relative.parts):
            record(f"forbidden path component in {relative_text}")
        folded_parts = tuple(component.casefold() for component in relative.parts)
        if any(
            folded_parts[index : index + 2] == (".agents", "plugins")
            for index in range(max(0, len(folded_parts) - 1))
        ):
            record(f"personal marketplace path is not allowed: {relative_text}")
        if any(
            folded_parts[index : index + 3]
            in ((".codex", "plugins", "cache"), (".claude", "plugins", "cache"))
            for index in range(max(0, len(folded_parts) - 2))
        ):
            record(f"plugin cache path is not allowed: {relative_text}")
        if any(component.casefold().endswith(".egg-info") for component in relative.parts):
            record(f"forbidden package residue in {relative_text}")
        lower_name = path.name.casefold()
        if lower_name in FORBIDDEN_FILENAMES or lower_name.startswith(".env"):
            record(f"forbidden file name: {relative_text}")
        if re.fullmatch(r"(?:credentials?|secrets?|tokens?)(?:[._-].*)?", lower_name):
            record(f"forbidden credential file name: {relative_text}")
        if path.is_file() and any(
            lower_name.endswith(suffix.casefold()) for suffix in FORBIDDEN_SUFFIXES
        ):
            record(f"forbidden generated or credential artifact: {relative_text}")
        if not path.is_file() and not path.is_dir():
            record(f"special filesystem entry is not allowed: {relative_text}")

        if not path.is_file():
            continue
        try:
            content = path.read_bytes()
        except OSError as error:
            record(f"cannot inspect file {relative_text}: {error}")
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            if path.suffix.casefold() not in ALLOWED_BINARY_SUFFIXES:
                record(f"unclassified binary or non-UTF-8 file is not allowed: {relative_text}")
            scan_text(relative_text, content.decode("utf-8", errors="ignore"), record)
        else:
            scan_text(relative_text, text, record)


def inspect_tree(root: Path) -> tuple[list[str], dict[str, Path]]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"repository root is not a directory: {root}"], {}
    inspect_required_files(root, errors)
    inspect_manifest(root, errors)
    skills = discover_skill_directories(root, errors)
    inspect_skill_wiring(root, skills, errors)
    inspect_repository_hygiene(root, errors)
    return errors, skills


def capture_tree_state(root: Path) -> dict[str, tuple[str, int, str]]:
    state: dict[str, tuple[str, int, str]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            kind = "symlink"
            digest = os.readlink(path)
        elif stat.S_ISREG(mode):
            kind = "file"
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        elif stat.S_ISDIR(mode):
            kind = "directory"
            digest = ""
        else:
            kind = "special"
            digest = ""
        state[relative.as_posix()] = (kind, stat.S_IMODE(mode), digest)
    return state


def describe_state_changes(
    before: dict[str, tuple[str, int, str]],
    after: dict[str, tuple[str, int, str]],
) -> list[str]:
    changes: list[str] = []
    before_paths = set(before)
    after_paths = set(after)
    changes.extend(f"added {path}" for path in sorted(after_paths - before_paths))
    changes.extend(f"removed {path}" for path in sorted(before_paths - after_paths))
    changes.extend(
        f"changed {path}"
        for path in sorted(before_paths & after_paths)
        if before[path] != after[path]
    )
    return changes


def run_regression_tests(root: Path) -> bool:
    tests = root / "tests"
    if not tests.is_dir():
        print("SKIP tests (no tests directory)")
        return True
    if tests.is_symlink():
        print("FAIL repository tests\ntests/ must not be a symlink.")
        return False
    test_files = sorted(path for path in tests.rglob("test_*.py") if path.is_file() and not path.is_symlink())
    if not test_files:
        print("FAIL repository tests\nNo test_*.py files were discovered under tests/.")
        return False
    layout_errors: list[str] = []
    for test_file in test_files:
        if not test_file.stem.isidentifier():
            layout_errors.append(
                f"test module {test_file.relative_to(root).as_posix()} is not importable by unittest"
            )
        parent = test_file.parent
        while parent != tests:
            if not parent.name.isidentifier():
                layout_errors.append(
                    f"nested test directory {parent.relative_to(root).as_posix()} is not a Python package name"
                )
                break
            if not (parent / "__init__.py").is_file():
                layout_errors.append(
                    f"nested test directory {parent.relative_to(root).as_posix()} is missing __init__.py"
                )
                break
            parent = parent.parent
    if layout_errors:
        print("FAIL repository tests")
        for error in sorted(set(layout_errors)):
            print(f"- {error}")
        return False

    before = capture_tree_state(root)
    tests_passed = run_command_requiring_output(
        "repository tests",
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        root,
        re.compile(r"\bRan [1-9][0-9]* tests?\b"),
    )
    after = capture_tree_state(root)
    changes = describe_state_changes(before, after)
    if changes:
        print("FAIL repository tests mutated the repository")
        for change in changes:
            print(f"- {change}")

    post_test_errors: list[str] = []
    inspect_repository_hygiene(root, post_test_errors)
    if post_test_errors:
        print("FAIL post-test repository hygiene")
        for error in post_test_errors:
            print(f"- {error}")
    return tests_passed and not changes and not post_test_errors


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = DEFAULT_ROOT
    plugin_validator, skill_validator = validator_paths()

    missing_validators = [
        str(path)
        for path in (plugin_validator, skill_validator)
        if not path.is_file()
    ]
    if missing_validators:
        print("Codex plugin/skill validators are unavailable:", file=sys.stderr)
        for path in missing_validators:
            print(f"- {path}", file=sys.stderr)
        return 2

    print(f"Using plugin validator: {plugin_validator}")
    print(f"Using skill validator: {skill_validator}")
    before_gate = capture_tree_state(root)

    errors, skills = inspect_tree(root)
    ok = not errors
    for error in errors:
        print(f"FAIL repository tree: {error}")
    if not errors:
        print("PASS repository tree")

    ok = run_command("plugin manifest", [sys.executable, "-B", str(plugin_validator), str(root)], root) and ok
    for skill_name in sorted(EXPECTED_SKILLS):
        skill_path = skills.get(skill_name, root / "skills" / skill_name)
        ok = run_command(
            f"skill {skill_name}",
            [sys.executable, "-B", str(skill_validator), str(skill_path)],
            root,
        ) and ok

    if args.skip_tests:
        print("SKIP repository tests (--skip-tests)")
    else:
        ok = run_regression_tests(root) and ok

    gate_changes = describe_state_changes(before_gate, capture_tree_state(root))
    if gate_changes:
        print("FAIL validation commands mutated the repository")
        for change in gate_changes:
            print(f"- {change}")
        ok = False

    if ok:
        print("Repository validation passed.")
        return 0
    print("Repository validation failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
