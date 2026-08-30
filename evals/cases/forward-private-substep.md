# Audit a hierarchical implication proof

Use `$forward-lamport` to audit the submitted hierarchical proof exactly as written. Do not replace it with another proof.

## Theorem

For propositions `A`, `B`, and `C`, assume `A ⇒ B` and `B ⇒ C`. Prove `A ⇒ C`.

## Submitted proof

```text
⟨1⟩1. ASSUME A PROVE B
  ⟨2⟩1. B
          Proof: By A and the theorem assumption A ⇒ B.
  ⟨2⟩2. Q.E.D.
⟨1⟩2. ASSUME A PROVE C
  ⟨2⟩3. C
          Proof: By ⟨2⟩1 and the theorem assumption B ⇒ C.
  ⟨2⟩4. Q.E.D.
⟨1⟩3. Q.E.D.
        Proof: By ⟨1⟩2.
```

## Accepted primitives

Modus ponens and implication introduction.
