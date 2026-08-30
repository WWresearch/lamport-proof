# Trace a polynomial-identity proof

Use `$reverse-lamport` to audit only the route supplied below.

## Theorem

For all real `x` and `y`, `(x + y)² = x² + 2xy + y²`.

## Submitted proof

- Claim C1: `(x + y)² = x² + 2xy + y²`, because Claim C2 can be rearranged to this equation.
- Claim C2: `2xy = (x + y)² - x² - y²`, because Claim C1 can be rearranged to this equation.
- The theorem follows from Claim C1.

## Accepted primitives

Equality reflexivity and reversible rearrangement of an established equation are accepted. The polynomial expansion itself is not an accepted primitive for this audit.
