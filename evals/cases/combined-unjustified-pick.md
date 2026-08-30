# Convert and audit a finite-set proof

Use `$convert-lamport` to create a source-mapped rendering without repairing the proof. Freeze that exact rendering. Use `$forward-lamport` on it, followed by `$reverse-lamport` using the same theorem contract and the forward audit's legal step ledger. Keep all three outcomes separate.

## Theorem

Every nonempty finite subset `S` of the real numbers is bounded above.

## Submitted proof

Pick `m ∈ S` such that every `s ∈ S` satisfies `s ≤ m`. Hence `S` is bounded above.

## Accepted primitives

The definitions of finite set, nonempty set, maximum, and bounded above. No existence theorem for a maximum is accepted as primitive.
