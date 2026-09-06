# Changelog

All notable changes to Lamport Proof are documented in this file.

The project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The historical `v0.1.0` tag is retained under its original package identity.

## [0.2.0] - 2026-09-06

### Added

- `$convert-lamport`, a source-preserving conversion skill with explicit mapping, support, gap, and ambiguity records.
- A deterministic behavioral eval corpus covering conversion and both audit directions.
- Behavioral coverage for all five forward verdicts and the partial-conversion-to-forward-audit boundary.
- Isolated local skill staging without modifying an existing Codex home.
- Contributor, citation, security, issue, pull-request, Code of Conduct, and CI material for public development.

### Changed

- Shortened the package and project name from `lamport-proof-toolkit` to `lamport-proof`.
- Renamed `$audit-lamport-proof` to `$forward-lamport` to distinguish it from `$reverse-lamport`.
- Reframed the toolkit as the three-stage `convert-lamport` → `forward-lamport` → `reverse-lamport` workflow.
- Rewrote the public description around inspecting hierarchy, dependencies, scope, and unresolved obligations.
- Strengthened public boundaries around model-assisted reports, source preservation, and non-certifying outcomes.
- Separated normalized mathematical content from Lamport scaffolding in conversion ledgers and made missing proof input a terminal source boundary rather than a proof gap.
- Clarified that a valid forward step still receives a minor finding when its written citation omits the active fact that supplies a nontrivial side condition.
- Preserved forward `FAIL` severity for converter-exposed unsupported internal assertions instead of treating an `OPEN` mapping record as deliberately omitted support.
- Required every unresolved conversion issue to retain a distinct `OBLIGATION` ledger row instead of being represented only by its source-content row.

### Compatibility

- No alias is provided for `$audit-lamport-proof`.
- `$reverse-lamport` retains its identifier, so old and new installations must not be enabled together.

## [0.1.0] - 2026-08-28

### Added

- Initial licensed standalone snapshot under the `lamport-proof-toolkit` name.
- `$audit-lamport-proof` for forward audits of submitted Lamport-style hierarchies.
- `$reverse-lamport` for conclusion-first audits of proof-supplied obligation routes.
- MIT licensing, authorship, provenance, and standalone repository checks.

[0.2.0]: https://github.com/WWresearch/lamport-proof/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/WWresearch/lamport-proof/releases/tag/v0.1.0
