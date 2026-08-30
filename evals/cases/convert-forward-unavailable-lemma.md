# Convert and audit a cited-lemma proof

Use `$convert-lamport` to render the source without supplying missing mathematics. Freeze the rendering, then use `$forward-lamport` to audit it.

## Theorem

For every real `x > 0`, `ln(x) ≤ x - 1`.

## Submitted proof

Apply Lemma T from the omitted appendix. This gives `ln(x) ≤ x - 1`, as required.

## Source boundary

The appendix and the exact statement and proof of Lemma T are not supplied. Standard ordered-field arithmetic is accepted, but the logarithm inequality itself is not an accepted primitive.
