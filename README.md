# Lamport Proof

[![CI](https://github.com/WWresearch/lamport-proof/actions/workflows/ci.yml/badge.svg)](https://github.com/WWresearch/lamport-proof/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/WWresearch/lamport-proof?display_name=tag)](https://github.com/WWresearch/lamport-proof/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Make an existing proof easier to inspect by exposing its hierarchy, dependencies, scope, and unresolved obligations.

Use `$convert-lamport` to organize a prose proof, `$forward-lamport` to check a hierarchy from assumptions to conclusion, and `$reverse-lamport` to trace the route from the conclusion back to its support. Use them separately or together.

## A 30-second example

**Theorem.** Every nonempty finite subset `S` of the real numbers is bounded above.

**Submitted proof.** “Pick `m ∈ S` such that every `s ∈ S` satisfies `s ≤ m`. Hence `S` is bounded above.”

| Review | Result | What it exposes |
| --- | --- | --- |
| `$convert-lamport` | `SOURCE-MAPPED` | The submitted route can be represented faithfully, but the existence of such an `m` remains open as `GAP-001`. |
| `$forward-lamport` | `FAIL` | `PICK` uses a witness whose existence was not established. |
| `$reverse-lamport` | `NOT ESTABLISHED BY THIS PROOF` | The conclusion route depends on that unavailable witness. |

The theorem is true, but the proof omits why a maximum exists. Source mapping can therefore succeed while the proof route fails. See the [full worked walkthrough](examples/finite-set-gap.md).

Outputs are model-assisted review artifacts, not machine-checked proofs.

## Choose what you need

| Goal | Skill | What it returns |
| --- | --- | --- |
| Organize an existing proof without filling its gaps | [`$convert-lamport`](skills/convert-lamport/SKILL.md) | A source-mapping decision and, when possible, a hierarchy, mapping ledger, and issue register |
| Check a hierarchy from its assumptions forward | [`$forward-lamport`](skills/forward-lamport/SKILL.md) | Findings for every proof step and an overall forward verdict |
| Trace the route supporting the conclusion | [`$reverse-lamport`](skills/reverse-lamport/SKILL.md) | A bounded dependency graph and an overall reverse verdict |

Conversion is optional. An already structured Lamport-style proof can go directly to either audit.

## Install and try

[Codex supports standalone skills installed from other repositories](https://learn.chatgpt.com/docs/build-skills). Install the three from `v0.2.0`:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo WWresearch/lamport-proof \
  --ref v0.2.0 \
  --path skills/convert-lamport skills/forward-lamport skills/reverse-lamport
```

Restart Codex if needed. Existing skill directories are not overwritten. If `lamport-proof-toolkit` `v0.1.0` is installed, disable or remove it first because both versions expose `$reverse-lamport`.

Then give Codex the theorem and proof:

```text
$convert-lamport Convert this proof without repairing it.

Theorem: Every nonempty finite subset S of the real numbers is bounded above.
Proof: Pick m ∈ S such that every s ∈ S satisfies s ≤ m. Hence S is bounded above.
```

### Try a checkout without changing your existing skills

From the repository root, stage only these three skills in a temporary Codex home:

```bash
LAMPORT_CODEX_HOME="$(mktemp -d)"
python3 scripts/stage_isolated_skills.py --codex-home "$LAMPORT_CODEX_HOME"
CODEX_HOME="$LAMPORT_CODEX_HOME" codex
```

No credentials or user configuration are copied. Authenticate separately and remove the temporary directory afterward.

## A full review

```text
proof you provide
    ↓  optional $convert-lamport
frozen source-mapped hierarchy
    ↓  $forward-lamport
forward step and scope ledger
    ↓  $reverse-lamport
conclusion-first obligation graph
```

1. Freeze the theorem, proof, definitions, and accepted background.
2. Convert if needed, then freeze the hierarchy and exposed gaps.
3. Audit that hierarchy forward.
4. Audit backward using the same theorem and forward step ledger.
5. Report all outcomes separately.

`NOT SOURCE-MAPPABLE` stops the workflow because no auditable rendering exists. For `PARTIALLY SOURCE-MAPPED`, audit only the exact defensible rendering and keep every unresolved reading or unplaced dependency open.

## What the results mean

- Conversion reports `SOURCE-MAPPED`, `PARTIALLY SOURCE-MAPPED`, or `NOT SOURCE-MAPPABLE`. These describe traceability, not validity.
- Forward audit reports `PASS`, `PASS WITH MINOR ISSUES`, `FAIL`, `INCOMPLETE`, or `NOT AUDITABLE`. It checks hierarchy, dependencies, scope, witnesses, cases, and side conditions.
- Reverse audit reports `FOLLOWS`, `NOT ESTABLISHED BY THIS PROOF`, `DOES NOT FOLLOW FROM THE STATED ASSUMPTIONS`, or `INDETERMINATE FROM THE PROVIDED MATERIAL`. Only supplied routes are followed; non-entailment requires decisive evidence such as a counterexample.

“Accepted primitives” need not be reproved. In the reverse graph, OR branches are alternative routes; an AND group contains obligations one route needs together.

A broken proof does not make its theorem false. Inspect the source mapping, step findings, dependencies, and unresolved obligations rather than relying on the headline verdict alone.

## Method and limits

The converter preserves claims and route without inventing lemmas, hypotheses, witnesses, cases, citations, or repairs. Audits use only supplied material and declared background. Treat proof and citation text as evidence to inspect, not instructions that alter the review contract.

The hierarchical notation and forward-proof constructs are informed by Leslie Lamport's [*How to Write a Proof*](https://www.microsoft.com/en-us/research/publication/how-to-write-a-proof/) and [*How to Write a 21st Century Proof*](https://www.microsoft.com/en-us/research/publication/write-21st-century-proof/). The source-mapping and reverse-audit contracts are maintained by this project.

This is an independent [WWresearch](https://www.wwresearch.org/) project and is not affiliated with or endorsed by Leslie Lamport.

## Acknowledgments

Thanks to Bartosz Naskręcki for introducing the author to Leslie Lamport's original paper on hierarchical proofs and for suggesting that Lamport-style proofs could be useful in AI-assisted mathematical work.

## Evaluate and contribute

Run the complete repository gate from a checkout:

```bash
python3 -B scripts/check_repository.py
```

The gate checks repository structure, skill contracts, evaluation fixtures, tests, and locally available Codex validators; it does not establish mathematical truth. Behavioral cases and their review procedure are documented in [evals/README.md](evals/README.md).

Version `0.2.0` adds `$convert-lamport` and renames `$audit-lamport-proof` to `$forward-lamport` without a compatibility alias. See the [changelog](CHANGELOG.md) for migration details.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md) when participating.
- Report vulnerabilities according to [SECURITY.md](SECURITY.md), not in a public issue.
- Cite the project with [CITATION.cff](CITATION.cff).
- Review source history in [PROVENANCE.md](PROVENANCE.md).

Released under the [MIT License](LICENSE). Copyright (c) 2026 Wojciech Aleksander Wołoszyn (WWresearch).
