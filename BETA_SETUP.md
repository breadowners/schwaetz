# Owner setup: compare models before opening the beta

The repository is public at https://github.com/breadowners/schwatz. A public beta
is not deployed. First choose a model using the existing personal app as a quality
reference. This setup is for the owner only; eventual testers will not need keys.

## 1. Set up the owner account

Sign in at https://openrouter.ai and open https://openrouter.ai/settings/credits.
For the first test, a small one-time purchase such as US$10 is enough account
credit to begin; the checkout shows the actual fees. Leave automatic top-ups off.
Purchasing credits is the owner's decision and is not performed by this project.

At https://openrouter.ai/settings/keys, create a separate standard API key named
`Schwatz model comparison`. Set its credit limit to **US$1** and choose **no reset**
(a lifetime limit). A daily or monthly resetting limit is not accepted by the
runner. Do not use an unlimited or broadly funded production key for this test.
The account can hold more credit; this key can access at most its own cap.

## 2. Run the prepared comparison

From the repository directory on your Mac, check the selected models without any
key or generation request:

```sh
.venv/bin/python benchmark_openrouter.py --list --allow-paid z-ai/glm-5.3-flash deepseek/deepseek-v4.1-flash-1017
```

Then start the actual comparison when you want to authorize paid requests:

```sh
.venv/bin/python benchmark_openrouter.py --allow-paid z-ai/glm-5.3-flash deepseek/deepseek-v4.1-flash-1017 --output paid-model-comparison.json
```

Paste the key into the hidden terminal prompt. It is held in process memory and
is not saved by the runner. It may alternatively read `OPENROUTER_API_KEY` from an
existing local environment. Do not put the key in a command argument, public file,
issue, conversation or screenshot. Neither this script nor the app loads `.env`
files automatically.

This run makes 18 generation requests: nine original synthetic text cases for
each explicit model. It checks the non-resetting provider cap before every paid
completion, does not retry automatically or substitute models, and saves progress
under ignored `.cache/paid-model-comparison.json`. It never sends your notes or
recordings. A current catalog listing does not establish account access or uptime.

The US$1 key limit is the maximum permitted exposure, not an estimate that the
comparison will cost US$1. Actual token usage may cost much less; OpenRouter's
Activity page is the billing reference. The runner's output contains model text
and timings, not keys or full account metadata. Re-running this comparison uses
the same lifetime key allowance until the owner changes or replaces it.

## 3. Review, then build access controls

Ask a fluent Luxembourgish speaker to compare unnecessary corrections, corrected
grammar, meaning preservation and translation errors. Review response times and
format failures separately. These short synthetic checks are an initial screen,
not proof of accuracy on learner recordings or equivalence across providers.

Once the model is selected, implement the shared-key beta, invitations, persistent
quotas, bounded speech queue and feedback capture in [BETA_PLAN.md](BETA_PLAN.md).
Resolve the existing speech-model/content permissions for the intended public,
donation-supported deployment, test load, then invite 10, 25 and up to 100 people.
Buying credit does not publish the app or configure any of those controls.
