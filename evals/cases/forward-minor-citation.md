# Review a hierarchical cancellation proof

Use `$forward-lamport` to audit the submitted hierarchical proof exactly as written. Do not replace it with a differently organized proof.

## Theorem

For every real number `x`, if `x ≠ 0`, then `x / x = 1`.

## Submitted proof

```text
⟨1⟩1. x / x = 1
        Proof: By cancellation.
⟨1⟩2. Q.E.D.
        Proof: By ⟨1⟩1.
```

## Accepted primitives

The field laws for the real numbers, including cancellation by a nonzero element, and the theorem assumption `x ≠ 0`.
