#!/usr/bin/env python3
"""Validate the standalone Lamport Proof repository."""

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
EXPECTED_VERSION = "0.2.0"
EXPECTED_AUTHOR = "Wojciech Aleksander Wołoszyn (WWresearch)"
EXPECTED_CONTACT = "contact@wwresearch.org"
EXPECTED_DEVELOPER = "WWresearch"
EXPECTED_WEBSITE = "https://www.wwresearch.org/"
EXPECTED_REPOSITORY = "https://github.com/WWresearch/lamport-proof"
EXPECTED_PLUGIN_NAME = "lamport-proof"
SKILL_ORDER = ("convert-lamport", "forward-lamport", "reverse-lamport")
EXPECTED_SKILLS = frozenset(SKILL_ORDER)
EXPECTED_EVAL_CASES = frozenset(
    {
        "combined-unjustified-pick",
        "convert-ambiguous-admitted-source",
        "convert-forward-unavailable-lemma",
        "convert-forward-valid-export",
        "convert-no-proof",
        "forward-private-substep",
        "reverse-circular-identity",
        "reverse-false-sign-loss",
        "reverse-unavailable-theorem",
        "reverse-valid-even-square",
    }
)
CONVERSION_STATUSES = frozenset(
    {"SOURCE-MAPPED", "PARTIALLY SOURCE-MAPPED", "NOT SOURCE-MAPPABLE"}
)
MAPPING_KINDS = frozenset({"DIRECT", "NORMALIZED", "STRUCTURAL", "OBLIGATION"})
SUPPORT_STATUSES = frozenset(
    {"EXPLICIT", "IMPLICIT", "EXTERNAL UNAVAILABLE", "ADMITTED", "OPEN", "AMBIGUOUS"}
)
FORWARD_VERDICTS = frozenset(
    {"PASS", "PASS WITH MINOR ISSUES", "INCOMPLETE", "FAIL", "NOT AUDITABLE"}
)
REVERSE_VERDICTS = frozenset(
    {
        "FOLLOWS",
        "NOT ESTABLISHED BY THIS PROOF",
        "DOES NOT FOLLOW FROM THE STATED ASSUMPTIONS",
        "INDETERMINATE FROM THE PROVIDED MATERIAL",
    }
)
OUTCOME_LOADED_EVAL_TITLE = re.compile(
    r"\b(?:admission|admitted|ambiguous|circular|false|illegal|invalid|"
    r"missing|unavailable|unjustified|valid)\b|\bsign branch\b|"
    r"\bno (?:submitted )?proof\b",
    re.IGNORECASE,
)
REQUIRED_ROOT_FILES = (
    ".codex-plugin/plugin.json",
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/skill-behavior.yml",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    "CHANGELOG.md",
    "CITATION.cff",
    "CONTRIBUTING.md",
    "LICENSE",
    "PROVENANCE.md",
    "README.md",
    "SECURITY.md",
    "evals/README.md",
    "evals/manifest.json",
    "scripts/check_repository.py",
    "scripts/stage_isolated_skills.py",
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
        description="Validate the standalone Lamport Proof repository."
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Run structural and Codex validators without repository regression tests.",
    )
    parser.add_argument(
        "--skip-codex-validators",
        action="store_true",
        help="Skip environment-owned Codex validators but retain tree and regression checks.",
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


def is_path_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


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
    if manifest.get("version") != EXPECTED_VERSION:
        errors.append(f"manifest version must be {EXPECTED_VERSION!r}")
    if manifest.get("repository") != EXPECTED_REPOSITORY:
        errors.append(f"manifest repository must be {EXPECTED_REPOSITORY!r}")
    if manifest.get("skills") != "./skills/":
        errors.append("manifest skills path must be './skills/'")
    if manifest.get("license") != "MIT":
        errors.append("manifest license must be 'MIT'")

    author = manifest.get("author")
    if not isinstance(author, dict) or author.get("name") != EXPECTED_AUTHOR:
        errors.append(f"manifest author.name must be {EXPECTED_AUTHOR!r}")
    if not isinstance(author, dict) or author.get("email") != EXPECTED_CONTACT:
        errors.append(f"manifest author.email must be {EXPECTED_CONTACT!r}")
    if not isinstance(author, dict) or author.get("url") != EXPECTED_WEBSITE:
        errors.append(f"manifest author.url must be {EXPECTED_WEBSITE!r}")
    if manifest.get("homepage") != EXPECTED_WEBSITE:
        errors.append(f"manifest homepage must be {EXPECTED_WEBSITE!r}")

    interface = manifest.get("interface")
    if not isinstance(interface, dict) or interface.get("developerName") != EXPECTED_DEVELOPER:
        errors.append(f"manifest interface.developerName must be {EXPECTED_DEVELOPER!r}")
    if not isinstance(interface, dict) or interface.get("websiteURL") != EXPECTED_WEBSITE:
        errors.append(f"manifest interface.websiteURL must be {EXPECTED_WEBSITE!r}")
    if not isinstance(interface, dict) or interface.get("displayName") != "Lamport Proof":
        errors.append("manifest interface.displayName must be 'Lamport Proof'")
    if not isinstance(interface, dict) or interface.get("capabilities") != ["Analyze", "Write"]:
        errors.append("manifest interface.capabilities must be ['Analyze', 'Write']")
    prompts = interface.get("defaultPrompt") if isinstance(interface, dict) else None
    if (
        not isinstance(prompts, list)
        or len(prompts) != 3
        or not all(isinstance(prompt, str) and 0 < len(prompt) <= 128 for prompt in prompts)
    ):
        errors.append("manifest interface.defaultPrompt must contain exactly three nonempty strings of at most 128 characters")
    else:
        lowered_prompts = [prompt.casefold() for prompt in prompts]
        if not any("convert" in prompt and "lamport" in prompt for prompt in lowered_prompts):
            errors.append("manifest starter prompts must cover Lamport conversion")
        if not any("forward" in prompt and "audit" in prompt for prompt in lowered_prompts):
            errors.append("manifest starter prompts must cover the forward hierarchy audit")
        if not any("backward" in prompt or "obligation" in prompt for prompt in lowered_prompts):
            errors.append("manifest starter prompts must cover the reverse obligation audit")


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

    readme_path = root / "README.md"
    if readme_path.is_file():
        try:
            readme_text = readme_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"cannot read README.md as UTF-8: {error}")
        else:
            if "`NOT SOURCE-MAPPABLE` stops the workflow" not in readme_text:
                errors.append("README.md must document the NOT SOURCE-MAPPABLE stop rule")
            if "`PARTIALLY SOURCE-MAPPED`" not in readme_text or "exact defensible rendering" not in readme_text:
                errors.append("README.md must document the partial-rendering audit boundary")


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
        errors.append(
            "skill inventory must contain exactly the three Lamport Proof skills"
            + (f" ({', '.join(details)})" if details else "")
        )
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

    convert = skill_texts.get("convert-lamport", "")
    forward = skill_texts.get("forward-lamport", "")
    reverse = skill_texts.get("reverse-lamport", "")
    required_cross_references = {
        "convert-lamport": (convert, ("$forward-lamport", "$reverse-lamport")),
        "forward-lamport": (forward, ("$convert-lamport", "$reverse-lamport")),
        "reverse-lamport": (reverse, ("$convert-lamport", "$forward-lamport")),
    }
    for skill_name, (text, references) in required_cross_references.items():
        for reference in references:
            if text and reference not in text:
                errors.append(f"{skill_name} must reference {reference}")

    convert_invariants = (
        "Structural scaffolding must itself be a legal Lamport hierarchy",
        "later siblings must not cite its private descendants",
        "Ambiguity must not conceal missing support",
        "one identifier per underlying source-support defect",
        "accepted primitives explicitly supplied",
        "For `NOT SOURCE-MAPPABLE`, stop",
    )
    for invariant in convert_invariants:
        if convert and invariant not in convert:
            errors.append(f"convert-lamport must preserve contract invariant: {invariant}")
    reverse_invariants = (
        "Unavailability alone is not `missing`",
        "A `MAJOR` or `CRITICAL` step is failing support",
        "`unavailable support`",
        "exact meta-obligation",
    )
    for invariant in reverse_invariants:
        if reverse and invariant not in reverse:
            errors.append(f"reverse-lamport must preserve contract invariant: {invariant}")
    forward_invariants = (
        "exact meta-obligation",
        "silently unsupported internal assertion",
    )
    for invariant in forward_invariants:
        if forward and invariant not in forward:
            errors.append(f"forward-lamport must preserve contract invariant: {invariant}")

    worked_rendering = root / "skills/convert-lamport/references/worked-rendering.md"
    if not worked_rendering.is_file():
        errors.append("convert-lamport is missing references/worked-rendering.md")

    worked_audit = root / "skills/reverse-lamport/references/worked-audit.md"
    if not worked_audit.is_file():
        errors.append("reverse-lamport is missing references/worked-audit.md")


def load_eval_manifest(root: Path, errors: list[str]) -> dict[str, object] | None:
    path = root / "evals/manifest.json"
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_json_keys,
        )
    except FileNotFoundError:
        errors.append("missing evals/manifest.json")
        return None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        errors.append(f"invalid evals/manifest.json: {error}")
        return None
    if not isinstance(payload, dict):
        errors.append("evals/manifest.json must contain a JSON object")
        return None
    return payload


def validate_string_list(
    value: object,
    *,
    allowed: frozenset[str],
    label: str,
    errors: list[str],
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label} must be a list of strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label} must not contain duplicates")
    invalid = sorted(set(value) - allowed)
    if invalid:
        errors.append(f"{label} contains invalid values: {invalid}")
    return list(value)


def validate_eval_criteria(
    value: object,
    *,
    label: str,
    errors: list[str],
) -> set[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a nonempty list")
        return set()
    identifiers: set[str] = set()
    for index, criterion in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(criterion, dict):
            errors.append(f"{item_label} must be an object")
            continue
        if set(criterion) != {"id", "description"}:
            errors.append(f"{item_label} must contain exactly id and description")
        identifier = criterion.get("id")
        description = criterion.get("description")
        if not isinstance(identifier, str) or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) is None:
            errors.append(f"{item_label}.id must be lower-case hyphenated text")
        elif identifier in identifiers:
            errors.append(f"duplicate criterion id {identifier!r} in {label}")
        else:
            identifiers.add(identifier)
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{item_label}.description must be nonempty")
    return identifiers


def inspect_evals(root: Path, errors: list[str]) -> None:
    manifest = load_eval_manifest(root, errors)
    if manifest is None:
        return
    if manifest.get("schema_version") != 1:
        errors.append("eval manifest schema_version must be 1")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("eval manifest cases must be a nonempty list")
        return

    evals_root = (root / "evals").resolve()
    cases_root = (root / "evals/cases").resolve()
    seen_case_ids: set[str] = set()
    referenced_prompts: set[str] = set()
    conversion_coverage: set[str] = set()
    mapping_coverage: set[str] = set()
    support_coverage: set[str] = set()
    forward_coverage: set[str] = set()
    reverse_coverage: set[str] = set()
    full_pipeline_present = False
    gap_prefixes = {
        "GAP": "OPEN",
        "AMB": "AMBIGUOUS",
        "EXT": "EXTERNAL UNAVAILABLE",
        "ADM": "ADMITTED",
    }

    for index, case in enumerate(cases):
        label = f"eval case[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object")
            continue
        required_keys = {
            "id",
            "prompt",
            "skills",
            "expected",
            "required_observations",
            "prohibited_claims",
        }
        if set(case) != required_keys:
            errors.append(f"{label} must contain exactly {sorted(required_keys)}")

        case_id = case.get("id")
        if not isinstance(case_id, str) or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case_id) is None:
            errors.append(f"{label}.id must be lower-case hyphenated text")
            case_id = f"invalid-{index}"
        elif case_id in seen_case_ids:
            errors.append(f"duplicate eval case id {case_id!r}")
        else:
            seen_case_ids.add(case_id)
        case_label = f"eval case {case_id}"

        prompt_value = case.get("prompt")
        prompt_text = ""
        if not isinstance(prompt_value, str):
            errors.append(f"{case_label}.prompt must be a string")
        else:
            prompt_path = Path(prompt_value)
            expected_prompt = f"cases/{case_id}.md"
            if prompt_value != expected_prompt or prompt_path.is_absolute() or ".." in prompt_path.parts:
                errors.append(f"{case_label}.prompt must be {expected_prompt!r}")
            resolved_prompt = (evals_root / prompt_path).resolve(strict=False)
            if not is_path_within(resolved_prompt, cases_root):
                errors.append(f"{case_label}.prompt escapes evals/cases")
            elif not resolved_prompt.is_file():
                errors.append(f"{case_label}.prompt file is missing")
            else:
                referenced_prompts.add(resolved_prompt.relative_to(evals_root).as_posix())
                try:
                    prompt_text = resolved_prompt.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as error:
                    errors.append(f"cannot read {case_label}.prompt: {error}")
                else:
                    title = next(
                        (
                            line.removeprefix("# ").strip()
                            for line in prompt_text.splitlines()
                            if line.startswith("# ")
                        ),
                        "",
                    )
                    if not title:
                        errors.append(f"{case_label}.prompt must start with a level-one title")
                    elif OUTCOME_LOADED_EVAL_TITLE.search(title):
                        errors.append(
                            f"{case_label}.prompt title discloses an outcome-loaded diagnosis"
                        )

        skills = case.get("skills")
        ordered_skills: list[str] = []
        if not isinstance(skills, list) or not skills or not all(isinstance(item, str) for item in skills):
            errors.append(f"{case_label}.skills must be a nonempty list of strings")
        else:
            ordered_skills = list(skills)
            if len(ordered_skills) != len(set(ordered_skills)):
                errors.append(f"{case_label}.skills must not contain duplicates")
            unknown = sorted(set(ordered_skills) - EXPECTED_SKILLS)
            if unknown:
                errors.append(f"{case_label}.skills contains unknown skills: {unknown}")
            known_order = [name for name in SKILL_ORDER if name in ordered_skills]
            if ordered_skills != known_order:
                errors.append(f"{case_label}.skills must follow convert, forward, reverse order")
            if ordered_skills == list(SKILL_ORDER):
                full_pipeline_present = True
            for skill_name in ordered_skills:
                if f"${skill_name}" not in prompt_text:
                    errors.append(f"{case_label}.prompt must explicitly invoke ${skill_name}")

        expected = case.get("expected")
        expected_values: list[str] = []
        expected_axes = {
            {"convert-lamport": "conversion", "forward-lamport": "forward", "reverse-lamport": "reverse"}[name]
            for name in ordered_skills
            if name in EXPECTED_SKILLS
        }
        if not isinstance(expected, dict):
            errors.append(f"{case_label}.expected must be an object")
            expected = {}
        elif set(expected) != expected_axes:
            errors.append(f"{case_label}.expected axes must be {sorted(expected_axes)}")

        conversion = expected.get("conversion") if isinstance(expected, dict) else None
        if "conversion" in expected_axes:
            conversion_keys = {"status", "mapping_kinds", "support_statuses", "register_ids"}
            if not isinstance(conversion, dict) or set(conversion) != conversion_keys:
                errors.append(f"{case_label}.expected.conversion must contain exactly {sorted(conversion_keys)}")
            else:
                status = conversion.get("status")
                if not isinstance(status, str) or status not in CONVERSION_STATUSES:
                    errors.append(f"{case_label} has an invalid conversion status")
                else:
                    conversion_coverage.add(status)
                    expected_values.append(status)
                mapping_kinds = validate_string_list(
                    conversion.get("mapping_kinds"),
                    allowed=MAPPING_KINDS,
                    label=f"{case_label}.mapping_kinds",
                    errors=errors,
                )
                support_statuses = validate_string_list(
                    conversion.get("support_statuses"),
                    allowed=SUPPORT_STATUSES,
                    label=f"{case_label}.support_statuses",
                    errors=errors,
                )
                mapping_coverage.update(mapping_kinds)
                support_coverage.update(support_statuses)
                register_ids = conversion.get("register_ids")
                if not isinstance(register_ids, list) or not all(isinstance(item, str) for item in register_ids):
                    errors.append(f"{case_label}.register_ids must be a list of strings")
                    register_ids = []
                elif len(register_ids) != len(set(register_ids)):
                    errors.append(f"{case_label}.register_ids must not contain duplicates")
                for register_id in register_ids:
                    match = re.fullmatch(r"(GAP|AMB|EXT|ADM)-[0-9]{3}", register_id)
                    if match is None:
                        errors.append(f"{case_label} has invalid register id {register_id!r}")
                    elif gap_prefixes[match.group(1)] not in support_statuses:
                        errors.append(f"{case_label} register id {register_id!r} does not match its support status")
                for prefix, support_status in gap_prefixes.items():
                    if support_status in support_statuses and not any(
                        item.startswith(prefix + "-") for item in register_ids
                    ):
                        errors.append(f"{case_label} support status {support_status!r} requires a {prefix}-nnn id")
                if status == "NOT SOURCE-MAPPABLE" and (mapping_kinds or support_statuses or register_ids):
                    errors.append(f"{case_label} NOT SOURCE-MAPPABLE expectations must not claim a rendering")
                if status == "SOURCE-MAPPED" and "AMBIGUOUS" in support_statuses:
                    errors.append(f"{case_label} material ambiguity requires PARTIALLY SOURCE-MAPPED")

        forward = expected.get("forward") if isinstance(expected, dict) else None
        if "forward" in expected_axes:
            if not isinstance(forward, str) or forward not in FORWARD_VERDICTS:
                errors.append(f"{case_label} has an invalid forward verdict")
            else:
                forward_coverage.add(forward)
                expected_values.append(forward)
        reverse = expected.get("reverse") if isinstance(expected, dict) else None
        if "reverse" in expected_axes:
            if not isinstance(reverse, str) or reverse not in REVERSE_VERDICTS:
                errors.append(f"{case_label} has an invalid reverse verdict")
            else:
                reverse_coverage.add(reverse)
                expected_values.append(reverse)

        criterion_ids = validate_eval_criteria(
            case.get("required_observations"),
            label=f"{case_label}.required_observations",
            errors=errors,
        )
        prohibited_ids = validate_eval_criteria(
            case.get("prohibited_claims"),
            label=f"{case_label}.prohibited_claims",
            errors=errors,
        )
        overlap = sorted(criterion_ids & prohibited_ids)
        if overlap:
            errors.append(f"{case_label} repeats criterion ids across rubric sections: {overlap}")

        for line in prompt_text.splitlines():
            folded = line.casefold()
            if not any(marker in folded for marker in ("expected", "required verdict", "required status", "answer should")):
                continue
            for value in expected_values:
                if value.casefold() in folded:
                    errors.append(f"{case_label}.prompt discloses expected outcome {value!r}")

    if seen_case_ids != EXPECTED_EVAL_CASES:
        missing = sorted(EXPECTED_EVAL_CASES - seen_case_ids)
        extra = sorted(seen_case_ids - EXPECTED_EVAL_CASES)
        errors.append(f"eval case inventory mismatch (missing={missing}, extra={extra})")

    if cases_root.is_dir():
        actual_prompts = {
            path.resolve().relative_to(evals_root).as_posix()
            for path in cases_root.glob("*.md")
            if path.is_file() and not path.is_symlink()
        }
        orphaned = sorted(actual_prompts - referenced_prompts)
        if orphaned:
            errors.append(f"orphan eval prompt files: {orphaned}")
    if conversion_coverage != CONVERSION_STATUSES:
        errors.append(f"evals must cover all conversion statuses: {sorted(CONVERSION_STATUSES)}")
    if mapping_coverage != MAPPING_KINDS:
        errors.append(f"evals must cover all mapping kinds: {sorted(MAPPING_KINDS)}")
    if support_coverage != SUPPORT_STATUSES:
        errors.append(f"evals must cover all support statuses: {sorted(SUPPORT_STATUSES)}")
    if not {"PASS", "FAIL", "INCOMPLETE"}.issubset(forward_coverage):
        errors.append("evals must cover forward PASS, FAIL, and INCOMPLETE")
    if reverse_coverage != REVERSE_VERDICTS:
        errors.append(f"evals must cover all reverse verdicts: {sorted(REVERSE_VERDICTS)}")
    if not full_pipeline_present:
        errors.append("evals must include the complete convert-forward-reverse pipeline")

    eval_readme = root / "evals/README.md"
    if eval_readme.is_file():
        try:
            readme_text = eval_readme.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"cannot read evals/README.md: {error}")
        else:
            if "SOURCE-MAPPED" not in readme_text or "never evidence" not in readme_text:
                errors.append("evals/README.md must state that SOURCE-MAPPED is never proof evidence")
            if "required coverage signals" not in readme_text:
                errors.append("evals/README.md must define mapping and support score semantics")
            if "complete expected issue set" not in readme_text:
                errors.append("evals/README.md must define register-id score semantics")
            if "saved files and digests" not in readme_text:
                errors.append("evals/README.md must require artifact-identity evidence")


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
    inspect_evals(root, errors)
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

    if not args.skip_codex_validators:
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

    before_gate = capture_tree_state(root)

    errors, skills = inspect_tree(root)
    ok = not errors
    for error in errors:
        print(f"FAIL repository tree: {error}")
    if not errors:
        print("PASS repository tree")

    if args.skip_codex_validators:
        print("SKIP Codex plugin/skill validators (--skip-codex-validators)")
    else:
        print(f"Using plugin validator: {plugin_validator}")
        print(f"Using skill validator: {skill_validator}")
        ok = run_command(
            "plugin manifest",
            [sys.executable, "-B", str(plugin_validator), str(root)],
            root,
        ) and ok
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
