# Lamport Proof

[![CI](https://github.com/WWresearch/lamport-proof/actions/workflows/ci.yml/badge.svg)](https://github.com/WWresearch/lamport-proof/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/WWresearch/lamport-proof?display_name=tag)](https://github.com/WWresearch/lamport-proof/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Convert · Forward · Reverse**

Lamport Proof is an independent [WWresearch](https://www.wwresearch.org/) toolkit of Codex skills for converting an existing proof into a source-mapped Lamport-style hierarchy and auditing a submitted proof in two complementary directions.

The toolkit produces model-assisted conversion and audit reports. It is not a proof assistant, a proof checker, or a formal-verification certificate. “Lamport” refers descriptively to the hierarchical proof style discussed in Leslie Lamport's publications; Leslie Lamport did not author, review, sponsor, or endorse this project.

## Choose a skill

| Skill | Input and direction | Primary question | Main output |
| --- | --- | --- | --- |
| `$convert-lamport` | Existing prose or loosely organized proof | How can the submitted proof be represented as a Lamport-style hierarchy without repairing or adding mathematics? | Source-mapped rendering, mapping ledger, and explicit gap register |
| `$forward-lamport` | Forward through an existing hierarchy | Does this submitted hierarchy establish its theorem with valid scope, dependencies, and construct use? | Findings, forward verdict, and complete step ledger |
| `$reverse-lamport` | Backward from the stated conclusion | Which proof-supplied AND/OR routes support the conclusion, and where does each route stop? | Obligation graph, dependency table, and reverse verdict |

Use `$convert-lamport` only when a proof needs a hierarchical representation. An already structured Lamport-style proof can go directly to `$forward-lamport` or `$reverse-lamport`.

## Complete workflow

```text
ordinary submitted proof
        ↓  $convert-lamport
source-mapped Lamport-style rendering
        ↓  $forward-lamport
forward hierarchy and scope verdict
        ↓  $reverse-lamport
conclusion-first obligation verdict
```

For a combined review:

1. Freeze one exact theorem statement, source boundary, and set of accepted primitives.
2. Run `$convert-lamport` if the submitted proof is not already hierarchical.
3. Check the conversion status. `NOT SOURCE-MAPPABLE` stops the workflow because no audit object exists. For `PARTIALLY SOURCE-MAPPED`, continue only on the exact defensible rendering and keep every unresolved reading open.
4. Freeze the converted rendering and its source-mapping ledger; do not revise it during the audits.
5. Run `$forward-lamport` on the frozen hierarchy.
6. Run `$reverse-lamport` last against the same theorem contract and the legal forward ledger.
7. Report conversion status, forward verdict, and reverse verdict separately.

Conversion annotations establish provenance, not mathematical support. `SOURCE-MAPPED` therefore does not imply `PASS` or `FOLLOWS`. A forward failure also does not by itself show that a theorem is false: the reverse audit distinguishes a broken submitted route from a genuine counterexample or other decisive non-entailment argument.

## Install from GitHub

Install the three skills directly from the versioned repository with the Codex system skill installer:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo WWresearch/lamport-proof \
  --ref v0.2.0 \
  --path skills/convert-lamport skills/forward-lamport skills/reverse-lamport
```

Restart Codex after installation so it discovers the new skills. The installer refuses to overwrite an existing destination. Remove or relocate an older installation deliberately before reinstalling; do not merge skill directories by hand.

Version `0.2.0` and the historical `0.1.0` package both expose `$reverse-lamport`. Disable or remove the old `lamport-proof-toolkit` installation before installing this release to avoid duplicate skill discovery.

## Use the skills

Invoke a single skill explicitly when you want one artifact:

```text
$convert-lamport Convert this submitted proof without repairing its gaps.
```

```text
$forward-lamport Audit this hierarchical proof for scope, construct use, and validity.
```

```text
$reverse-lamport Trace the supplied proof route backward as an AND/OR obligation graph.
```

For a complete review, request the three skills in that order and require separate outcomes. Supply the exact theorem, the complete submitted proof, nonstandard definitions, and any external results that the audit may treat as available. Missing external material remains an explicit open obligation.

The converter preserves the proof's submitted route and defects. It must not invent lemmas, hypotheses, witnesses, cases, citations, or repairs. The audits evaluate only the supplied material and accepted background; they do not silently replace the proof with a better one.

## Isolated local development

To test a checkout without changing globally installed Codex skills, create a temporary Codex home and stage only this repository's three skills:

```bash
LAMPORT_CODEX_HOME="$(mktemp -d)"
python3 scripts/stage_isolated_skills.py --codex-home "$LAMPORT_CODEX_HOME"
CODEX_HOME="$LAMPORT_CODEX_HOME" codex
```

The staging helper refuses the active global Codex home, destinations inside the repository, symlinked destinations, and existing skill directories. It copies neither credentials nor user configuration. Authentication for the isolated session must be provided independently through the normal Codex login or environment mechanism.

Delete the temporary directory after testing. Do not point `--codex-home` at a Codex home that contains work you intend to keep.

## Outcome boundaries

The three skills have independent outcome systems:

- Conversion reports `SOURCE-MAPPED`, `PARTIALLY SOURCE-MAPPED`, or `NOT SOURCE-MAPPABLE`.
- Forward audit reports `PASS`, `PASS WITH MINOR ISSUES`, `FAIL`, `INCOMPLETE`, or `NOT AUDITABLE`.
- Reverse audit reports `FOLLOWS`, `NOT ESTABLISHED BY THIS PROOF`, `DOES NOT FOLLOW FROM THE STATED ASSUMPTIONS`, or `INDETERMINATE FROM THE PROVIDED MATERIAL`.

These labels describe a structured review performed from the supplied material. They do not claim kernel-checked certainty. Review the mapping ledger, step ledger, obligation graph, unresolved items, and cited sources rather than relying on a headline verdict alone.

## Repository checks

From the checkout root, run the full local gate:

```bash
python3 -B scripts/check_repository.py
```

The gate checks package metadata, exact skill inventory, cross-skill routing, public repository invariants, eval fixtures, hygiene, tests, and all three skills with the locally installed official Codex validators. It checks repository structure and contracts; it does not establish the mathematical truth of an audited theorem.

CI uses the model-free form because the official Codex validators are not part of the runner environment:

```bash
python3 -B scripts/check_repository.py --skip-codex-validators
```

That flag skips only environment-owned validators. Repository checks, eval-schema validation, and tests still run. Behavioral eval responses are reviewed separately against the checked-in scorecards.

## Version migration

Version `0.2.0` shortens the public project name and expands the toolkit from two skills to three:

| `v0.1.0` | `v0.2.0` |
| --- | --- |
| `lamport-proof-toolkit` | `lamport-proof` |
| No conversion skill | `$convert-lamport` |
| `$audit-lamport-proof` | `$forward-lamport` |
| `$reverse-lamport` | `$reverse-lamport` |

There are no compatibility aliases. Prompts, scripts, or documentation that invoke `$audit-lamport-proof` must use `$forward-lamport` after upgrading.

## Method attribution

The hierarchical notation and proof constructs audited here are informed by Leslie Lamport's [*How to Write a Proof*](https://www.microsoft.com/en-us/research/publication/how-to-write-a-proof/) and [*How to Write a 21st Century Proof*](https://www.microsoft.com/en-us/research/publication/write-21st-century-proof/). Those publications are methodological references; their text is not distributed in this repository.

The source-mapping conversion contract, forward audit procedure, and `$reverse-lamport` conclusion-first audit method are maintained as part of this independent WWresearch project. In particular, `$reverse-lamport` is not a method authored or endorsed by Leslie Lamport.

## Project information

- Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes.
- Report vulnerabilities according to [SECURITY.md](SECURITY.md), not in a public issue.
- Cite the project with [CITATION.cff](CITATION.cff).
- See [CHANGELOG.md](CHANGELOG.md) for release history.

Published by [WWresearch](https://www.wwresearch.org/). Copyright (c) 2026 Wojciech Aleksander Wołoszyn (WWresearch).

Released under the [MIT License](LICENSE).
