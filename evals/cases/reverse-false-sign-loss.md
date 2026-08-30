# Trace an integer-square proof

Use `$reverse-lamport` to audit the submitted route and determine what the stated assumptions support.

## Theorem

For every integer `n`, if `n² = 1`, then `n = 1`.

## Submitted proof

From `n² = 1`, we get `(n - 1)(n + 1) = 0`. Therefore `n - 1 = 0`, so `n = 1`.

## Accepted primitives

Elementary integer arithmetic and the zero-product property.
