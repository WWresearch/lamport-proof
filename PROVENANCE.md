# Source provenance

The toolkit first entered version control on 2026-07-23 in the local `personal-codex-plugins` repository at commit `c6ff5a822bfa4e0a6ef9decf91548173e4fb108c`, under `plugins/lamport-proof-toolkit`. That repository had no configured remote when this standalone repository was established.

On 2026-08-28, the copyright holder split the toolkit into this standalone repository for explicit licensing and future development. The installed Codex snapshot `0.1.0+codex.20260723110547` matched the earlier Git source except for that cache-buster version suffix. The standalone source version was `0.1.0`; licensing, authorship, homepage, and attribution metadata were added without changing the substantive skill, agent, or worked-example files.

## Snapshot hashes before repository metadata changes

| Relative path | SHA-256 |
| --- | --- |
| `.codex-plugin/plugin.json` | `2e11855ddc7fd6f8ca6ab06661762b2ea377ec562d8010b168e3bca37ac4620b` |
| `README.md` | `edb267f810c2cd91a74fcbdddb0459755c76490d3885c857ec5acf83ac69e885` |
| `skills/audit-lamport-proof/SKILL.md` | `24dfcb7361c9608dbfce1fa1e65d0f07b6b734cb7a862e95b4347f3413562338` |
| `skills/audit-lamport-proof/agents/openai.yaml` | `4d5320fd723f54ff57c4f380a34940fa9be411b8f8310a581e0aaa5da3af8b0b` |
| `skills/reverse-lamport/SKILL.md` | `4505d1d61de1164a0767205f98cdb5f53cb366da0fd54ae452118323a345571a` |
| `skills/reverse-lamport/agents/openai.yaml` | `041942b7ab5eb9ab6a3f78230cc406dec8bfc20240e915c0fb400875424ed17d` |
| `skills/reverse-lamport/references/worked-audit.md` | `c271a85a30a17d0283ede4ff9ba3841f58a3a99fed47ed931cf49767b41d9152` |

The absolute cache location is intentionally omitted so this provenance record remains portable and does not disclose workstation-specific paths.

## Version 0.2.0 lineage

On 2026-08-31, the standalone project was prepared locally for a `0.2.0` release under the shorter name `lamport-proof`. This release adds a source-preserving conversion skill and gives the forward and reverse audits symmetric public identifiers.

| Version 0.1.0 | Version 0.2.0 | Disposition |
| --- | --- | --- |
| `lamport-proof-toolkit` | `lamport-proof` | Standalone package renamed. |
| No conversion skill | `$convert-lamport` | New source-mapped presentation conversion; it does not repair proofs. |
| `$audit-lamport-proof` | `$forward-lamport` | Identifier renamed; the forward audit contract is preserved. |
| `$reverse-lamport` | `$reverse-lamport` | Identifier preserved; routing references are updated. |

The `v0.1.0` snapshot hashes above intentionally retain their historical paths and names. They are not hashes of the renamed `0.2.0` files.

## Repository publication

This standalone repository is intended to supersede the `personal-codex-plugins` subtree as the editable source for Lamport Proof. The predecessor remains a historical `0.1.0` snapshot; its redirect is prepared independently so unrelated work in that repository is not disturbed.

The publication URL selected during local preparation was `https://github.com/WWresearch/lamport-proof`, and the plugin manifest records the same URL. As of the local `0.2.0` preparation on 2026-08-31, no Git remote had been configured and no GitHub repository had been created. Those statements record the preparation boundary rather than the repository's eventual publication state. The local `v0.1.0` tag identified the initial licensed standalone release; the local annotated `v0.2.0` tag identified the prepared renamed release.
