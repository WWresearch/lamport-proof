# Lamport Proof Toolkit

Two complementary skills audit an existing proof without generating a replacement:

| Skill | Direction | Primary question | Main output |
| --- | --- | --- | --- |
| `audit-lamport-proof` | Forward through the submitted hierarchy | Does this Lamport-style proof establish its theorem with valid scope and construct use? | Findings and a complete step ledger |
| `reverse-lamport` | Backward from the stated conclusion | Which proof-supplied AND/OR routes support the conclusion, and where does each stop? | Obligation graph and dependency table |

Use the forward skill for numbered hierarchical proofs, `ASSUME/PROVE`, `SUFFICES`, `PICK`, `CASE`, `DEFINE`, and `Q.E.D.` semantics. Use the reverse skill for conclusion-first dependency reconstruction, hidden assumptions, route switches, and bounded support analysis of routes supplied by the proof. It does not search for a different proof to settle full theorem-level entailment. Neither skill audits proof-assistant source as Lean, Coq, or Isabelle code.

## Running both audits

1. Freeze one theorem statement, source boundary, and set of accepted primitives.
2. Run `audit-lamport-proof` first to establish the forward step ledger and legal scope.
3. Run `reverse-lamport` second from the exact conclusion, rechecking every proposition and dependency edge.
4. Report the two verdicts separately.

The verdicts answer different questions and must not be collapsed:

| Forward verdict | Typical reverse verdict | Meaning |
| --- | --- | --- |
| `PASS` or `PASS WITH MINOR ISSUES` | `FOLLOWS` | The submitted route establishes the conclusion; any noted defects are non-invalidating. |
| `FAIL` | `NOT ESTABLISHED BY THIS PROOF` | The submitted proof has a decisive gap; this alone does not show the conclusion is false. |
| `FAIL` | `DOES NOT FOLLOW FROM THE STATED ASSUMPTIONS` | The proof fails and a counterexample, countermodel, or decisive non-entailment argument establishes non-entailment. |
| `INCOMPLETE` | `INDETERMINATE FROM THE PROVIDED MATERIAL` | Missing external or omitted material prevents closure. |
| `NOT AUDITABLE` | `INDETERMINATE FROM THE PROVIDED MATERIAL` | The supplied theorem or proof does not support either reconstruction. |

These are expected alignments, not automatic conversions. If the two audits disagree unexpectedly, recheck that they used the same theorem contract, source boundary, and accepted primitives.

## Method attribution

The forward audit targets the hierarchical proof style described by Leslie Lamport in [*How to Write a Proof*](https://www.microsoft.com/en-us/research/publication/how-to-write-a-proof/) and [*How to Write a 21st Century Proof*](https://www.microsoft.com/en-us/research/publication/write-21st-century-proof/). Those publications are methodological references; their text is not distributed in this toolkit.

`reverse-lamport` is a conclusion-first audit technique developed for this WWresearch toolkit. It is not a method authored or endorsed by Leslie Lamport.

## Authorship and license

Published by [WWresearch](https://www.wwresearch.org/). Copyright (c) 2026 Wojciech Aleksander Wołoszyn (WWresearch).

Released under the [MIT License](LICENSE).

## Validation

From the checkout root, run the standalone repository gate:

```bash
python3 -B scripts/check_repository.py
```

The gate validates the plugin manifest and both skills with the current Codex validators, checks the exact toolkit skill inventory, cross-skill references, worked example, licensing and provenance metadata, and UI prompt wiring, rejects symlinks, generated residue, credential artifacts, workflow markers, and workstation-specific paths, and runs Python `unittest` discovery whenever a `tests/` directory is present. It fails if tests are absent from a present test directory, mutate distributable repository contents, or leave new residue.

Use `--skip-tests` only when isolating structural or Codex-validator failures. The full command above is the required repository gate.

The script resolves the repository relative to its own location, so invoking it by an absolute or relative path also works from another working directory.

This is a developer gate for the distributable repository tree, not a sandbox or a release-state check. It treats the installed Codex validators and checked-in tests as trusted local code. It does not enforce a Git branch, clean worktree, tag, remote, or publication decision; those checks belong in a separate release workflow.
