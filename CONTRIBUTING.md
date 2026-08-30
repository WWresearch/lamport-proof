# Contributing to Lamport Proof

Thank you for helping improve Lamport Proof. Contributions should make the three skill contracts clearer, more reliable, or easier to evaluate without overstating what a model-assisted proof review establishes.

## Project boundaries

The public interfaces are `$convert-lamport`, `$forward-lamport`, and `$reverse-lamport`.

- The converter restructures only the submitted proof. It must preserve the theorem, route, assumptions, strength, and defects, and must expose unsupported material rather than repair it.
- The forward auditor checks the submitted Lamport-style hierarchy, including scope, construct semantics, dependencies, and side conditions. It does not generate a replacement proof.
- The reverse auditor reconstructs conclusion-reachable routes supplied by the proof. It does not perform unbounded proof search or substitute a different proof.
- Conversion status, forward verdict, and reverse verdict are separate axes. Do not add automatic mappings that collapse them.
- Project outputs are review artifacts, not proof-checker results or formal-verification certificates.

Changes that intentionally alter a skill's mission, input boundary, output sections, status taxonomy, or verdict meaning require an explicit design discussion before implementation.

## Set up an isolated checkout

Use Python 3.10 or newer. Clone the repository, then stage the skills in a disposable Codex home so development does not alter your existing installation:

```bash
LAMPORT_CODEX_HOME="$(mktemp -d)"
python3 scripts/stage_isolated_skills.py --codex-home "$LAMPORT_CODEX_HOME"
CODEX_HOME="$LAMPORT_CODEX_HOME" codex
```

Provide authentication independently for the isolated session. Remove the temporary directory after testing.

## Make a focused change

1. Start from `main` and create a short-lived branch.
2. Keep the change within one clear concern: skill contract, example, eval, repository check, or documentation.
3. Preserve exact source boundaries and outcome wording in examples.
4. Add or update a deterministic eval case for any behavioral change.
5. Keep eval prompts independent of their expected answers and record required observations and prohibited silent repairs in the scorecard.
6. Update public documentation when an identifier, workflow, or user-visible contract changes.

Do not include credentials, generated session output, local paths, installed-skill copies, caches, or model transcripts in a contribution.

## Validate the change

Run the complete local gate before opening a pull request:

```bash
python3 -B scripts/check_repository.py
```

The full gate requires the locally installed official Codex validators. The CI-equivalent command is:

```bash
python3 -B scripts/check_repository.py --skip-codex-validators
```

Also confirm:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

For a skill-behavior change, run the affected cases in fresh isolated sessions and review the complete output against each semantic scorecard. A schema-valid eval is not evidence that the behavior passed.

## Pull requests

Explain:

- the problem and intended behavior;
- which skill contracts or repository interfaces change;
- how source preservation and outcome boundaries remain intact;
- which checks and behavioral cases you ran;
- any user-visible migration required.

Small, reviewable pull requests are preferred. Maintainers may request a narrower change or additional adversarial cases when a proposed instruction could silently strengthen, repair, or certify a proof.

Report suspected vulnerabilities privately as described in [SECURITY.md](SECURITY.md). Use a public issue for reproducible skill behavior, documentation, packaging, and evaluation problems that do not expose a vulnerability.

## License of contributions

This project does not require a contributor license agreement or Developer Certificate of Origin. By submitting a contribution, you agree that it may be distributed under the project's [MIT License](LICENSE) and that you have the right to provide it on those terms.
