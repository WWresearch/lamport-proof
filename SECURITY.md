# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| `main` | Yes |
| Latest `0.2.x` release | Yes |
| `0.1.x` and earlier | No |

Support covers the repository's current skill instructions, helper scripts, validation code, and distribution metadata.

## Report a vulnerability

Do not open a public issue for a suspected vulnerability. Use either private channel:

- [GitHub private vulnerability reporting](https://github.com/WWresearch/lamport-proof/security/advisories/new); or
- email [contact@wwresearch.org](mailto:contact@wwresearch.org) with the subject `[lamport-proof security]`.

Include, when available:

- the affected version, commit, skill, or script;
- the security impact and realistic attack conditions;
- minimal reproduction steps or a proof of concept;
- any known mitigation;
- whether and where the issue has already been disclosed.

Do not send credentials, personal data, or unrelated confidential material. If the report itself requires a protected transfer method, request one in the initial email before sending sensitive details.

WWresearch will aim to acknowledge a report within seven days, assess its scope, and provide status updates while a fix or disclosure plan is being prepared. Please allow a reasonable remediation period before public disclosure.

## Skill behavior versus security

An incorrect conversion, missed proof defect, disputed mathematical judgment, or inconsistent model response is normally a skill-behavior issue, not a security vulnerability. Report those cases with the public skill-behavior issue form after removing private material.

Treat all generated reports as untrusted review output. Inspect them before reuse, do not execute commands copied from submitted proof text, and do not rely on a verdict as mathematical certification.
