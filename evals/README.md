# Behavioral evaluations

This corpus tests the observable contracts of `$convert-lamport`, `$forward-lamport`, and `$reverse-lamport`. Each case is self-contained and declares its expected axes, semantic observations, and prohibited shortcuts in `manifest.json`.

Repository tests validate the corpus structure and coverage without invoking a model. They do not establish that a model satisfies the rubrics.

When scoring a response, require the declared conversion status and audit verdicts exactly. Treat `mapping_kinds` and `support_statuses` as required coverage signals: additional uses are acceptable only when they are source-faithful and contract-compliant. Treat `register_ids` as the complete expected issue set; an unexplained missing or additional issue fails the case. Every `required_observation` must be present semantically, and any `prohibited_claim` fails the case even when the headline outcome is correct.

For a behavioral release check:

1. Stage the three skills under an isolated `CODEX_HOME` outside this checkout.
2. Run every single-skill stage in a fresh ephemeral session.
3. For a multi-skill case, run conversion alone and save its exact output outside the repository. Record its SHA-256 digest.
4. Run the forward audit in a new session using that saved conversion as the proof input; do not give it the original prose as an alternative proof object. Save and hash the complete forward output.
5. Run the reverse audit, when requested, in another new session using the same conversion and the exact saved forward ledger. Include the two recorded digests in the handoff and do not let the model independently reparse the original prose.
6. Store responses, digests, and scorecards outside the repository.
7. Review the expected status or verdict, every required observation, and every prohibited claim manually.

Do not run a multi-skill case as one unconstrained response and call that artifact identity. The saved files and digests are evaluation evidence that each downstream stage consumed the frozen upstream artifact.

Do not grade mathematical behavior with keyword or regular-expression matching. In particular, `SOURCE-MAPPED` is a traceability status and never evidence that a proof is valid.
