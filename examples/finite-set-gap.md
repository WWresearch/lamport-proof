# A Finite-Set Proof with an Unjustified Witness

> **Curated example.** This walkthrough is derived from the checked-in [`combined-unjustified-pick`](../evals/cases/combined-unjustified-pick.md) evaluation and its semantic requirements in [`evals/manifest.json`](../evals/manifest.json). It is not a verbatim Codex response or a prescribed transcript. Exact wording and node labels may vary, but the three outcomes and the observations below are required by the evaluation.

## Material supplied for review

**Theorem.** Every nonempty finite subset `S` of the real numbers is bounded above.

**Submitted proof.**

> Pick `m ∈ S` such that every `s ∈ S` satisfies `s ≤ m`. Hence `S` is bounded above.

**Accepted primitives.** The definitions of finite set, nonempty set, maximum, and bounded above. No theorem establishing the existence of a maximum is accepted as a primitive.

The proof's route is clear: use a maximum of `S` as an upper bound. Its unresolved step is the existence of that maximum.

## 1. Source-preserving conversion

`$convert-lamport` must preserve the route instead of supplying the familiar argument that a nonempty finite set of real numbers has a maximum.

A concise conceptual rendering is:

```text
<1>1. PICK m ∈ S such that every s ∈ S satisfies s ≤ m
      required first: ∃m ∈ S such that ∀s ∈ S, s ≤ m
      support: OPEN — GAP-001
<1>2. S is bounded above
      BY <1>1 and the definition of bounded above
<1>3. Q.E.D.
```

This trimmed hierarchy illustrates the required issue; it is not canonical generated output. Because `GAP-001` remains open, the source's later use of `m` is retained for traceability but does not make the witness legally available.

The expected conversion status is `SOURCE-MAPPED`. Every proof-bearing sentence can be placed, so the source is traceable even though its support is incomplete. The mapping uses `DIRECT`, `STRUCTURAL`, and `OBLIGATION`, with both `EXPLICIT` and `OPEN` support:

| Source material | Rendered role | Mapping | Support | Issue |
| --- | --- | --- | --- | --- |
| `SRC-001` — The theorem | Frozen theorem contract | `DIRECT` | `EXPLICIT` | — |
| `SRC-002` — “Pick `m`...” | `PICK` structure | `STRUCTURAL` | `EXPLICIT` | — |
| `SRC-002` — Existence required before `PICK` | Exact existence obligation | `OBLIGATION` | `OPEN` | `GAP-001` |
| `SRC-003` — “Hence...” | Boundedness conclusion | `DIRECT` | `EXPLICIT`, dependent on the failed introduction | `GAP-001` |

`GAP-001` records one underlying defect: the proof supplies no argument that an element satisfying the `PICK` condition exists. Recording the obligation is not evidence for it, and successful source mapping does not discharge it.

## 2. Forward audit

A `PICK m ∈ S : P(m)` step must first establish:

```text
∃m ∈ S : P(m)
```

Only after that existence proof succeeds may the fresh witness `m`, its membership in `S`, and the property `P(m)` enter scope.

Here, the proof immediately uses the proposed maximum but identifies no supplied theorem, admitted derivation, or available external result that could establish its existence. The `PICK` step therefore has a major internal defect, and the boundedness step inherits the unavailable witness.

The expected forward verdict is:

```text
FAIL
```

The failure belongs to this proof route. The auditor must not repair it by inserting induction, an order-theoretic theorem, or another proof that was not supplied.

## 3. Reverse audit

The reverse audit begins with the conclusion that `S` is bounded above and follows only the route used by the proof:

```text
C1  S is bounded above
    └── AND route: use a maximum as an upper bound
        ├── O1  ∃m ∈ S such that ∀s ∈ S, s ≤ m
        │        missing support — GAP-001
        └── O2  any such m is a real upper bound
                 from S ⊆ ℝ and the definition of bounded above
```

The forward ledger has already established that the witness never became legally available. The reverse audit must preserve that result rather than reinterpret the words “Pick `m`” as proof that such an element exists.

The expected reverse verdict is:

```text
NOT ESTABLISHED BY THIS PROOF
```

No sufficient route supplied by the proof closes. This verdict does not say that the theorem is false, and it does not rule out a different proof.

## The three outcomes remain separate

| Question | Outcome |
| --- | --- |
| Can the source be represented faithfully? | `SOURCE-MAPPED` |
| Does the resulting hierarchy establish the theorem? | `FAIL` |
| Does the submitted conclusion-reachable route close? | `NOT ESTABLISHED BY THIS PROOF` |

That distinction is the point of the example. Conversion records where each claim came from. Forward audit checks whether the hierarchical steps are valid and legally scoped. Reverse audit checks whether the dependencies used by the conclusion close. None of the stages may use another stage's formatting or metadata as mathematical evidence.
