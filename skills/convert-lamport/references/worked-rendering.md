# Worked source-mapped rendering

This example calibrates source mapping when a submitted proof asserts a step with “clearly” but supplies no argument. It illustrates conversion only; it does not audit the resulting proof.

## Submitted material

**Theorem.** For every real number `x`, `x^2 + 1 \ge 1`.

**Proof.** “Clearly `x^2 \ge 0`, so adding `1` gives `x^2 + 1 \ge 1`.”

No other definitions, lemmas, or citations are supplied.

## 1. Rendering status

**SOURCE-MAPPED.** Every proof-bearing source segment is placed. The justification of `x^2 \ge 0` remains open as `GAP-001`.

This status concerns source mapping only; it is not a validity verdict.

## 2. Frozen source contract

- Domain: `x \in \mathbb{R}`.
- Conclusion: `x^2 + 1 \ge 1`.
- Supplied proof: the two quoted source clauses above.
- Accepted primitives: none explicitly supplied.
- External-material boundary: none supplied or invoked.
- Transcription assumptions: none.

## 3. Source inventory

| Source ID | Source segment | Role | Placement |
| --- | --- | --- | --- |
| `SRC-001` | “Clearly `x^2 \ge 0`” | Intermediate assertion with no supplied support | `⟨1⟩1`, `GAP-001` |
| `SRC-002` | “so adding `1` gives `x^2 + 1 \ge 1`” | Transition to the conclusion | `⟨1⟩2` |

## 4. Lamport-style rendering

```text
THEOREM. For every x ∈ ℝ, x² + 1 ≥ 1.

PROOF.
⟨1⟩1. x² ≥ 0.
        Proof: OPEN — GAP-001. The source says only “Clearly.”
⟨1⟩2. x² + 1 ≥ 1.
        Proof: By ⟨1⟩1, adding 1 to both sides, as stated in SRC-002.
⟨1⟩3. Q.E.D.
        Proof: By ⟨1⟩2.
```

`GAP-001` is intentionally not filled with a familiar fact about real squares. Doing so would repair or complete the source rather than convert it.

## 5. Source-to-step mapping ledger

| Rendered step / item | Source ID(s) | Mapping kind | Source support | Issue ID | Notes |
| --- | --- | --- | --- | --- | --- |
| Frozen theorem contract | Theorem statement | `NORMALIZED` | `EXPLICIT` | — | Normalizes “for every real number `x`” as `x \in \mathbb{R}` without changing the proposition. |
| `⟨1⟩1` | `SRC-001` | `DIRECT` | `OPEN` | `GAP-001` | The assertion is explicit; its proof is not supplied. |
| Proof obligation at `⟨1⟩1` | `SRC-001` | `OBLIGATION` | `OPEN` | `GAP-001` | Required support is exposed, not invented. |
| `⟨1⟩2` | `SRC-002` | `NORMALIZED` | `EXPLICIT` | — | Normalizes “adding 1” into the displayed inequality. |
| `⟨1⟩3` | `SRC-002` | `STRUCTURAL` | `IMPLICIT` | — | Makes the source's conclusion transition explicit. |

## 6. Gap and ambiguity register

### `GAP-001` — `OPEN`

- Missing proposition or support: a justification of `x^2 \ge 0` for the fixed real `x`.
- Rendering location: proof of `⟨1⟩1`.
- Source: `SRC-001`.
- Downstream dependence: `⟨1⟩2` and `⟨1⟩3`.
- Material needed to close it: a source-supplied argument or an explicitly accepted background fact establishing nonnegativity of real squares.

## 7. Frozen audit handoff

The theorem contract, empty accepted-primitive set, three rendered steps, mappings, and `GAP-001` are fixed for audit. The phrase “Clearly” and the source-map ledger establish provenance only; neither discharges `GAP-001`. A forward audit must decide the step from the accepted proof boundary rather than silently adding a proof during conversion.
