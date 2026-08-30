# Convert and audit an implication proof

Use `$convert-lamport` to render the submitted proof as a source-mapped Lamport-style hierarchy without adding mathematical content. Freeze that rendering, then use `$forward-lamport` to audit the frozen hierarchy.

## Theorem

For propositions `A`, `B`, and `C`, assume `A ⇒ B` and `B ⇒ C`. Prove `A ⇒ C`.

## Submitted proof

Assume `A`. Since `A ⇒ B`, we obtain `B`. Since `B ⇒ C`, we obtain `C`. Therefore `A ⇒ C`.

## Accepted primitives

Modus ponens and implication introduction.
