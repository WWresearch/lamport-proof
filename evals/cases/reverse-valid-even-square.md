# Trace an even-square proof

Use `$reverse-lamport` to reconstruct only the conclusion-reachable route supplied by this proof.

## Theorem

For every integer `n`, if `n` is even, then `n²` is even.

## Submitted proof

Because `n` is even, there is an integer `k` with `n = 2k`. Hence `n² = 4k² = 2(2k²)`. Since `2k²` is an integer, `n²` is even.

## Accepted primitives

The definition of evenness and closure of the integers under multiplication.
