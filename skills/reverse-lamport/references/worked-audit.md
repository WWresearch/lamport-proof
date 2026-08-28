# Worked Reverse Lamport Audit

Use this example to calibrate granularity, classification, bounded alternatives, and the distinction between an invalid proof and a non-entailment result.

## Proof under audit

> **Claim.** Let $U\subseteq\mathbb R$ be open. If $f:U\to\mathbb R$ is differentiable and $f'(t)=0$ for every $t\in U$, then $f$ is constant on $U$.
>
> **Proof.** Take $x<y$ in $U$. By the mean value theorem, there is $c\in(x,y)$ such that
> \[
> f(y)-f(x)=f'(c)(y-x)=0.
> \]
> Hence $f(x)=f(y)$, so $f$ is constant.

## Audit boundary

- Conclusion `C0`: for all $x,y\in U$, $f(x)=f(y)$.
- Hypotheses: $U$ is open; $f$ is differentiable on $U$; $f'=0$ on $U$.
- Accepted primitives: definition of constant function, the mean value theorem with its standard interval hypotheses, differentiability implies continuity, and elementary real algebra and order rules.

## Obligation graph

```text
C0 <- R0, arbitrary-point comparison
      AND: O1, O9, C1

C1: f(x)=f(y) for arbitrary x<y in U
    <- R1, mean value theorem and zero derivative
       AND: O3, O4, O5

O2: the mean value theorem applies on [x,y]
    <- AND: O6, O7, O8

O3: there exists c in (x,y) with f(y)-f(x)=f'(c)(y-x)
    <- mean value theorem (AND: O2)

O4: f'(c)=0
    <- hypothesis instantiation (AND: O3, O8)

O5: the MVT identity and f'(c)=0 imply f(x)=f(y)
    <- elementary algebra

O6 <- differentiability-implies-continuity (AND: O8)
O7 <- restriction of the differentiability hypothesis (AND: O8)
```

Diagnostic comparison, not an alternative route to `C0`: the same MVT route closes when $x$ and $y$ lie in one connected component. The inability to bridge from componentwise to global constancy exposes the hidden requirement that $U$ be connected.

The primary route requires:

- `O1`: reducing constancy to equality at arbitrary $x,y\in U$;
- `O9`: reducing arbitrary pairs to $x<y$, equality, or the symmetric case;
- `O3`: a point $c\in(x,y)$ satisfying $f(y)-f(x)=f'(c)(y-x)$, supplied by the mean value theorem;
- `O4`: $f'(c)=0$;
- `O5`: the MVT identity together with $f'(c)=0$ implies $f(x)=f(y)$;
- `O6`: $f$ is continuous on $[x,y]$;
- `O7`: $f$ is differentiable on $(x,y)$;
- `O8`: $[x,y]\subseteq U$.

The hypotheses support `O6` and `O7` only when `O8` holds. Openness of $U$ does not imply `O8` for arbitrary points in different components.

## Critical findings

- `O8` is missing. The proof needs $U$ to be an interval, or at least needs arbitrary $x,y$ to lie in the same connected component.
- The universal application of the mean value theorem in `O2` is too strong relative to the hypotheses.
- The diagnostic componentwise comparison is mentioned only because it exposes the hidden connectedness assumption. It is not developed as a replacement proof.
- A counterexample settles entailment: take $U=(-2,-1)\cup(1,2)$, let $f=0$ on the first component, and let $f=1$ on the second. Then all stated hypotheses hold but the conclusion fails.

## Dependency table

| ID | Exact claim or obligation | Needed by | Route / edge | Classification | Support | Status |
| --- | --- | --- | --- | --- | --- | --- |
| C0 | $f$ is constant on $U$ | root | R0 / claim | root | definition via O1, O9, and C1 | failing |
| O1 | Constancy reduces to $f(x)=f(y)$ for arbitrary $x,y\in U$ | C0 | R0 / AND | definition | definition of constant | discharged |
| O9 | It suffices to prove equality for $x<y$, with equality trivial and $x>y$ handled symmetrically | C0 | R0 / AND | algebraic/logical step | trichotomy and symmetry of equality | discharged |
| C1 | $f(x)=f(y)$ for arbitrary $x<y$ in $U$ | C0 | R0 / AND | major claim | R1 | failing |
| O2 | MVT applies to arbitrary $x<y$ in $U$ | O3 | applicability / AND | too strong | valid only when O6--O8 hold | failing |
| O3 | There exists $c\in(x,y)$ with $f(y)-f(x)=f'(c)(y-x)$ | C1, O4 | MVT / AND | named theorem | mean value theorem; blocked by failing O2 | open |
| O4 | $f'(c)=0$ | C1 | hypothesis instantiation / AND | hypothesis | $f'=0$ on $U$; requires the witness from O3 and $c\in U$ via O8 | open |
| O5 | $[f(y)-f(x)=f'(c)(y-x)\ \text{and}\ f'(c)=0]\Rightarrow f(x)=f(y)$ | C1 | R1 / AND | algebraic/logical step | elementary algebra | discharged |
| O6 | $f$ is continuous on $[x,y]$ | O2 | applicability / AND | side condition | differentiability implies continuity where defined; blocked by O8 | open |
| O7 | $f$ is differentiable on $(x,y)$ | O2 | applicability / AND | side condition | differentiability on $U$; blocked by O8 | open |
| O8 | $[x,y]\subseteq U$ for arbitrary $x<y$ in $U$ | O2, O4, O6, O7 | applicability / AND | missing | openness does not imply interval containment | failing |

## Verdict

**DOES NOT FOLLOW FROM THE STATED ASSUMPTIONS.** The primary route fails at `O2` and `O8`, and the two-component counterexample shows that the conclusion itself is not entailed. Adding that $U$ is an interval would discharge the hidden domain obligation; with the stated assumptions, the strongest supported conclusion is constancy on each connected component.
