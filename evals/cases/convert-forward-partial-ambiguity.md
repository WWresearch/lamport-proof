# Convert and review a handwritten algebra proof

Use `$convert-lamport` to source-map only what the submitted material supports. Do not add missing support or choose between possible transcriptions. Freeze the exact defensible rendering and issue register, then use `$forward-lamport` to audit only that frozen rendering.

## Theorem

For real numbers `a` and `b`, if `a = b`, then `a² = b²`.

## Submitted proof

Put `u = a + b` and `v = a - b`. The next handwritten identifier is illegible: it is either `u` or `v`; the manuscript says that this identifier is zero. We admit without proof that `a² - b² = uv`. The manuscript uses that admitted identity together with its zero assertion to conclude `a² = b²`.

## Source boundary

No clearer image, transcription, or proof of the admitted identity is available. Do not choose the identifier according to which choice makes the argument succeed. The forward audit receives the frozen partial rendering, mapping ledger, and issue register, but not the original prose as an alternative proof object.
