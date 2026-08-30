## Summary

Describe the problem and the smallest change that addresses it.

## Contract impact

- [ ] No public skill identifier or output contract changes.
- [ ] Conversion remains source-preserving and does not silently repair mathematics.
- [ ] Conversion, forward, and reverse outcomes remain independent.
- [ ] User-facing changes and migrations are documented.

Explain any unchecked item:

## Verification

- [ ] `python3 -B scripts/check_repository.py`
- [ ] `python3 -B -m unittest discover -s tests -p 'test_*.py'`
- [ ] `git diff --check`
- [ ] Relevant behavioral cases were run in fresh isolated sessions.
- [ ] No credentials, local paths, caches, installed copies, or generated transcripts are included.

List the behavioral cases run and summarize their results:

## Security

- [ ] This pull request does not disclose an unpatched vulnerability.
