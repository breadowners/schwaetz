# Contributing to Schwätz

The application source is maintained at https://github.com/breadowners/schwatz
under Apache-2.0. Contributions to the code and original documentation use that
license. External models, dictionaries, recordings and course materials have
separate terms; read [THIRD_PARTY.md](THIRD_PARTY.md).

## Development

Use Python 3.12 and Node.js 24. For tests without downloading speech models:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm test
```

There are no npm dependencies to install. Tests use synthetic text/audio and
mocked model services; no private notes, API keys or model weights are required.
GitHub Actions is not configured yet; the current publishing authorization does
not include the `workflow` scope. Run the checks locally when submitting changes.
To run the full speech application, follow the model setup in [README.md](README.md).
The optional pronunciation runtime has additional dependencies and separate terms.

Keep changes focused and include the relevant verification in the pull request.
Python API tests live in `tests/test_*.py`; browser-flow unit tests use Node's test
runner in `tests/*.test.mjs`. These checks do not establish linguistic accuracy,
real-device browser behavior or production capacity.

## Report a problem or language correction

Use https://github.com/breadowners/schwatz/issues for ordinary bugs. Include what
you tried, what happened, the expected behavior, and your device/browser. For a
language correction, include a short invented example, the proposed correction
and a source you may share, such as an official dictionary link. Mark regional
variants and uncertain interpretations explicitly. A native-speaker review is
valuable; general model benchmarks do not validate Luxembourgish feedback.

Share synthetic examples in public issues and tests. Keep API keys, private notes,
class handouts, conversation exports, personal recordings, invitation codes and
usage databases out of issues, pull requests and Git history. Public mode must
continue to ignore a configured private vault. Report vulnerabilities privately
using [SECURITY.md](SECURITY.md).

Downloaded models and podcast recordings belong in the ignored local directories.
Keep source attribution and license notices when adapting third-party code. Do
not add full publisher transcripts or translations without permission to do so.

## Benchmarks

`benchmark_openrouter.py --list` checks whether its explicit shortlist is still
zero-priced, without a key or model completion. An actual benchmark uses a hidden
local terminal prompt or `OPENROUTER_API_KEY`; never paste a key into an issue or
chat. It sends original synthetic text only and records outputs for human review
in ignored `.cache/`. Successful JSON and response speed are not accuracy scores.
Free-only operation is the default. Paid comparisons require `--allow-paid`,
explicit model IDs, and a separate provider key with a positive lifetime limit of
US$1 or less and no automatic limit reset. The runner checks this before each
completion, with the provider enforcing the cap. See [BETA_SETUP.md](BETA_SETUP.md).
