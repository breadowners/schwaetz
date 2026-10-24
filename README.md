# Schwätz — Luxembourgish speaking and listening practice

A local, phone-friendly web app focused on pronunciation practice and spoken
conversations. Speech recognition, experimental sound checks and spoken examples
run on your computer. Conversation replies can use Ollama or supported free
OpenCode models. This repository contains the application source only.

The project lives at [breadowners/schwatz](https://github.com/breadowners/schwatz).
See [CONTRIBUTING.md](CONTRIBUTING.md) for development and language corrections,
[SECURITY.md](SECURITY.md) for private vulnerability reporting, and
[BETA_PLAN.md](BETA_PLAN.md) for the proposed rollout to up to 100 invited testers.
The public beta and its shared model budget are not deployed yet.
The owner's next step is [BETA_SETUP.md](BETA_SETUP.md): a model comparison using
a separate OpenRouter key with a non-resetting spending limit of US$1 or less.

## Quick start

Use Python 3.12, Node/npm for launch shortcuts, and a Mac (Apple Silicon is the
most tested setup). CPU inference is available on other systems. Choose either
an installed Ollama conversation model or [OpenCode v2](https://opencode.ai/v2/docs/)
for the optional online conversation route.

```sh
git clone https://github.com/breadowners/schwatz.git
cd schwatz
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-pronunciation.txt
.venv/bin/python download_models.py
.venv/bin/python download_models.py --pronunciation
npm run dev
```

Downloads include several gigabytes of models. Review [THIRD_PARTY.md](THIRD_PARTY.md)
for their separate terms. These are not included in the repository. Open
**http://localhost:8765** and allow microphone access when you begin practice.
Sounds practice works without a conversation model.

## Optional private lesson notes

A fresh clone provides fictional speaking situations and five starter words.
It does not need the author's course vault. To use your own compatible Obsidian
vault, start with `SPEAK_VAULT=/path/to/your/notes npm run dev`. A sibling clone at
`../luxembourgish-notes/notes` is detected automatically, with the original
`../notes` location as a fallback. `SPEAK_VAULT` always takes priority. Only the selected
sections listed in `content.py` are read; the app does not modify the vault.
The original A2.1 note layout is optional. Source labels distinguish built-in
practice from actual configured notes. Do not commit your notes or recordings.

## Source license

Application source: [Apache-2.0](LICENSE), copyright 2026 Mengxi He. See
[NOTICE](NOTICE) and [THIRD_PARTY.md](THIRD_PARTY.md) for adapted code, dependencies,
and model terms. An open-source application license does not relicense downloaded
model weights or make phonetic feedback a validated pronunciation assessment.

## Start on this Mac

```sh
cd schwatz
npm run dev
```

Open **http://localhost:8765**. In **Settings → Conversation model**, choose
**GLM 5.3 Flash · Free · OpenCode** or **DeepSeek V4.1 Flash · Free · OpenCode**
for online replies, or `qwen3.8:27b`
for local replies. GLM is the default for quicker replies. On the first refresh
after this update, the previous DeepSeek default moves to GLM; subsequent explicit
model choices and existing local/personal-key choices are preserved. Click **Start conversation**, listen, then speak your reply. When the model proposes
a corrected sentence or the separate audio model finds a possible sound mismatch,
the app pauses the conversation and **reads the correction aloud slowly**.
The large **Continue conversation** button resumes the held reply. Repeating is
optional: use the smaller **Record & check** microphone to get visible feedback
on a new attempt. For wording corrections, this shows the recognised sentence,
whether its transcript matches the example, and a separate experimental sound
check. A different transcript is a cue to compare, not a pronunciation or grammar
grade. If there is
both a sound tip and a wording correction, it first offers the next correction.
Repetitions do not become new conversation-model turns or discard your conversation.
**Listen** replays the example. Automatic correction audio has its own Settings
switch, separate from ordinary reply playback. Browser autoplay restrictions may
require pressing Replay or Listen once. The app keeps the last generated clip
ready to play directly on that tap and reuses the same speech player for later
replies. Sound checks remain experimental; examples use Piper.

The **Sounds** tab works without Qwen/Ollama: listen to the example, say the displayed **Say** phrase into
the microphone, and pause or tap again. Sound feedback compares the recording
with dictionary variants, gives up to two possible sound differences and practice
tips, reads the displayed example when a possible difference is detected, and can
replay the approximate part of your recording. Each tip also offers the target
word aloud and word practice. **Compare the sounds
(IPA)** shows the evidence. You can enter your own short phrase or analyse a
short audio file. Short words use “Ech soen…” (“I say…”) to give the phonetic
model more context; the prefix is generated practice, not a teacher quotation.

Recorded conversation turns also get separate sound feedback using the
recognised text as the assumed target. If the recognition is wrong, turn on
**Check my transcript first** and fix the target before sending. Typed replies
get wording feedback only, with spoken sentence corrections. Allow microphone access when your browser asks.

The interface uses a single column with Speak, Sounds and Listening tabs. Topic
selection is one dropdown; settings, lesson sources, IPA evidence and file input
are tucked away. There is no decorative hero, sidebar or motivational copy.

Settings include slower speech, English translations, checking the transcript
before sending, automatic end-of-turn detection, and continued conversation
(listen again automatically after your partner speaks). Recording stops when
the page is hidden and is capped at one minute per turn. You can interrupt a
spoken reply by tapping the microphone.

Eight situations cover restaurant, reservation, transport, neighbourhood,
housing and dream homes, household preferences, a cleaning rota, and open
everyday conversation. Housing uses Lesson 07's checked articles and grammar;
housework uses Lesson 08's vocabulary, preferences and separable verbs.
The correction flow lets you continue immediately or practise again with feedback. With the private vault,
Sounds reads the original 113 vocabulary entries and selected tables from
Lessons 07–08, including housing nouns, descriptions, chores and preferences.
New lesson words use local Piper examples; existing synthetic vocabulary clips
are reused for longer older entries. Pulling updates in the notes repository
updates these selected sections and tables without copying notes into the app.
A fresh clone without a vault uses five starter words. Conversations are held
in page memory; **Save conversation** explicitly downloads a Markdown copy.
Only preferences are saved automatically in this browser.

## Listening practice

Open **Listening** (or `/#listening`) for eight official INLL Poterkëscht episodes,
selected from the publisher's public RSS feed. Topics cover restaurant orders,
restaurant problems, reservations, banking, shops and opening hours, directions,
train tickets, housing, housework and introductions. The publisher's level and
publication date are shown; these are original recordings, not synthetic speech.

Use the normal player, 0.65×/0.8× playback and **Back 10 seconds**. Generated
comprehension questions are shown one at a time. Choose an answer before checking;
answer keys stay on the server until an attempt. Their evidence is the published
transcript, not an independently checked listening assessment or official exam.

**Transcript & English** reads the existing translated restaurant/bank and
directions/train transcripts from your private Mock Test 02 note, when configured.
These 144 aligned lines exclude test questions and answers. English is hidden by
default and labelled study support, not an official INLL translation. Other full
transcripts stay linked at the publisher. **Translate a passage** translates up to
1,500 characters you paste using your selected model; it does not send the audio
or your vault. The official A2 (2017) textbook companion pages are linked separately.

For a fresh machine, download the selected public originals with:

```sh
.venv/bin/python download_listening.py
```

Downloads are unchanged in `.cache/listening/`, outside Git; the catalog records
their publisher URLs and SHA-256 hashes. Without downloads, official source links
still work. Listening playback, transcripts and quiz feedback need no conversation
model. Generated passage translation uses the selected model and its normal
privacy/availability rules. Public mode ignores private translated notes.

The selected conversation model is remembered in Settings. When you start a
conversation, the app begins loading it while the opening plays, and keeps it
loaded for up to thirty idle minutes. Recorded conversation turns run sound
analysis and reply generation together after transcription. Sound evidence can
appear before the reply and remains available if the conversation request fails.

## Bring your own API key

Settings → Use your own API key supports an individual **OpenRouter** key.
The app verifies the key with the provider, loads its current model catalog,
and defaults to **Free models only**. Disabling this filter before connecting
allows models billed to that person's own provider account. Set a spending cap
on the key at [OpenRouter](https://openrouter.ai/settings/keys).

The key is kept in the current browser tab's JavaScript memory. The input is
cleared immediately; refreshing, leaving the page, or Disconnect clears it.
It is not written to localStorage, sessionStorage, the service-worker cache,
a database, files, or logs by this app. The key travels through this app's server
for each provider request and is kept only for that request's lifetime. Use HTTPS
for any hosted deployment. Only loopback development accepts HTTP.

Keys are attached only to the selected person's conversation and warm-up requests.
Speech recordings never go to OpenRouter. The provider receives the transcript,
recent conversation and selected practice context. Price metadata is rechecked
before every turn; an unavailable or no-longer-free model is rejected when the
free-only filter applies. There is no model or account fallback. Provider quotas,
privacy policies and free model availability still apply. A successful catalog
connection does not establish Luxembourgish grammar or pronunciation accuracy.

OpenCode's promotional free models are separate from OpenRouter's catalog.
An OpenCode token cannot be pasted into this connection to unlock those models.
OpenCode's [hosted-service terms](https://opencode.ai/legal/terms-of-service)
restrict use to internal use and exclude use for third parties' benefit;
permission for a shared public free-token backend must not be assumed. The
existing OpenCode runtime remains a personal/local feature.

## Public BYOK deployment mode

Start with `SPEAK_PUBLIC=1` for a deployment used by other people. This mode:

- Does not start or share the host's OpenCode runtime or Ollama model inventory.
- Requires each conversation request to carry that visitor's provider key.
- Ignores the private vault, even if one is present or configured.
- Uses built-in fictional practice and starter words, with explicit audio-hosting disclosure.
- Requires HTTPS for API-key requests. Speech analysis still runs on the host.

For example, behind a trusted HTTPS reverse proxy to localhost:

```sh
SPEAK_PUBLIC=1 SPEAK_ALLOWED_HOSTS=your-demo.example npm run dev
```

The API trusts forwarded HTTPS information only through Uvicorn's configured
trusted proxy behavior; keep the backend bound to localhost. Production hosting
still needs a stable HTTPS endpoint, bounded request/concurrency limits, resource
monitoring and rollout/rollback. This mode is a deployment foundation, not a
claim that a public service has already been deployed. BYOK covers language-model
usage; hosting the ZLS/ZIPA/Piper speech services still requires compute.

Provider-request tests use mocked keys/responses. The live unauthenticated model
catalog was checked; a successful real-key paid/free completion has not been tested
without an account key. API keys must be entered in the app, never in GitHub issues.

## Free conversation models through OpenCode

Requires an installed **OpenCode v2** (`opencode --version`). The server starts a
separate, authenticated OpenCode runtime on a random localhost port, in an empty
temporary directory. It does not use your personal OpenCode configuration or API
keys. It calls the documented transient session `/generate` API, which returns
text without running tools or appending the conversation to session history.
One empty context per model is reused to avoid creating and deleting a session
for every reply. No conversation messages are appended. The empty contexts,
runtime and temporary storage are removed on app shutdown.

The exact models are `opencode/glm-5.3-flash-free` and
`opencode/deepseek-v4.1-flash-free`. OpenCode's [model list](https://opencode.ai/v2/docs/console/models/)
lists both as free for a limited time as checked on 16 October 2026. Direct calls to
the hosted free API are rejected outside OpenCode; this integration uses the
official local runtime and its supported [application API](https://opencode.ai/v2/docs/api).
No account, payment details, or API key are used. Only these exact free models are
allowed, the selected model's catalog price is checked before each turn, and there is no paid
fallback. Quota, availability, and the promotion can change; a failure leaves the
attempt available for retry or lets you choose Qwen in Settings.

The reply path uses shorter instructions, removes link URLs and Markdown emphasis
from model excerpts, and requests brief spoken replies. The full selected source
remains available in Lesson source. GLM is the faster default based on local
timing samples; both free models remain selectable. Upstream speed and availability
vary, and shorter output does not establish better Luxembourgish accuracy.

Online mode sends your transcript, recent conversation, and the selected curated
lesson excerpt to OpenCode. It does not upload recordings, phonetic evidence,
whole source files, or raw class transcripts. OpenCode currently states that the
free models' providers have zero retention and do not train on requests. The
header says **Online** when selected; Settings explains what leaves the Mac.
Recognition, pronunciation checks, and Piper speech remain local. Better general
reasoning benchmarks do not establish better Luxembourgish grammar or pronunciation.

Set `SPEAK_DISABLE_OPENCODE=1` when starting the app to disable this runtime.
Set `SPEAK_MODEL=qwen3.8:27b` to prefer local replies on a fresh browser.

## Free local models

- Recognition: [ZLS Luxembourgish large-v3-turbo](https://huggingface.co/ZLSCompLing/Whisper-Large-V3-Turbo-Luxembourgish), model card identifies MIT licensing. This is a different model from LuxASR's closed university flagship. Download is approximately 3.2 GB. Apple Silicon uses the Metal encoder below plus a CPU float32 decoder with four threads; other platforms use CPU int8 with six threads. The checkpoint, beam size of three, language, and voice activity detection remain the same. Set `SPEAK_METAL_ENCODER=0 SPEAK_ASR_COMPUTE=int8 SPEAK_ASR_THREADS=6 npm run dev` to restore the original CPU settings.
- Local replies: your installed Ollama models, with `qwen3.8:27b` preferred when online replies are unavailable. Change it in Settings. The first turn can be slower while weights and the lesson prompt are loaded. This installed Qwen is already a Q4_K_M quantized build; its larger Q8 version is not a speed upgrade.
- Voice: [Marco Barnig's Luxembourgish femaleLOD Piper model](https://huggingface.co/mbarnig/lb_rhasspy_piper_tts), trained using ZLS data. The model card labels it CC BY 4.0; the linked [Open Data entry](https://data.public.lu/en/datasets/lb-rhasspy-piper-female-tts-2/) labels it CC BY-SA 4.0. Retain attribution and confirm the licensing discrepancy before redistribution. Downloaded models stay outside Git. Piper engine is GPL-3.0.
- Reference clips: existing synthetic ZLS study audio in the vault, generated 11 October 2026 and slowed to 75%; not independently checked by a native speaker.

No LuxASR API calls, paid model fallback, or cloud publication are enabled. Audio
inference runs on this Mac. With an Ollama model selected, conversation also stays
local; with either OpenCode model selected, the text described above goes to OpenCode.
Speech recordings are decoded in
memory and are not saved by the server. Browser recordings and sound feedback
remain in page memory for replay and disappear on reload or a session reset.
The launch script disables HTTP access logs because targets are in API URLs.

### Speech latency — 15 October 2026

On this M1 Max, alternating the previous int8/six-thread setting with
float32/four-thread inference across three synthetic recordings gave median
transcription times of **5.09 s → 4.26 s** (about 16% faster). All three transcript
texts matched. This is a small synthetic comparison, not a human-speech accuracy
evaluation; other CPU-intensive jobs were running, so absolute latency varies.
Results are in `.cache/asr-interleaved-benchmark.json`. A preliminary isolated
float32/four-thread pass was around 2.5–2.9 s, but that is not the paired result.

Replay audio is cached in memory (up to 24 examples / 8 MiB), including separate
slow/normal variants. This cache contains synthetic voice output only; microphone
recordings are never placed in it. Recognition and voice synthesis have separate
locks, so hearing an example does not queue behind a running transcription.

**Tap the microphone again when finished** for the quickest send. Automatic
finish now defaults to a **1.2-second** silence. Settings → Pause before sending
offers two- and three-second waits for more thinking time. The auto-stop switch
still lets you finish manually. ZIPA analysis and conversation generation run concurrently after
transcription. The slower correction voice is for listening practice and does not
make model processing slower.

### GPU transcription and conversation flow

On Apple Silicon, the app now loads the **encoder from the same local ZLS
checkpoint** into MLX, using original float32 weights and fused GPU attention.
CTranslate2 keeps the original decoder, three-beam search, tokenizer, and VAD.
The adapter reads the public CTranslate2 v6 / WhisperSpec v3 layout and checks
that every encoder tensor is mapped; it does not download a replacement model
or modify the original weights. MLX adds roughly 2.5 GB of resident weights.
GPU kernels warm up at startup, before the first recording. If initialization
or inference fails, the app uses the original CPU encoder on the same input.
Set `SPEAK_METAL_ENCODER=0` to force CPU transcription.

The repeatable validation run across three synthetic clips took **4.72–5.67 s
on CPU vs 0.81–1.99 s with the GPU encoder**, with matching transcripts.
Encoder differences are recorded per clip in the validation report. An earlier
direct comparison had RMSE around `1.4e-5` and maximum absolute difference around
`0.0018`. These checks establish numerical and sample transcript parity, not
validated learner-speech accuracy. Timings vary with CPU/GPU load and clip length.

Reproduce this locally with explicit test files (no audio is uploaded):

```sh
.venv/bin/python benchmark_speech.py path/to/synthetic-example.wav
```

The report `.cache/asr-metal-validation.json` records the source checkpoint hash,
encoder numerical comparison, transcripts and timings. See the
[MLX Whisper encoder](https://github.com/ml-explore/mlx-examples/tree/main/whisper)
and [CTranslate2's encoded-feature API](https://opennmt.net/CTranslate2/python/ctranslate2.models.Whisper.html).

Two live synthetic end-to-end turns (transcription → parallel ZIPA/DeepSeek →
first example/reply WAV ready) took **9.94–11.10 s before vs 4.67–5.22 s after**.
These times exclude recording, the silence wait, and spoken playback duration.
The free provider's latency varies, so this is a small smoke comparison rather
than a guaranteed response time. Stage timings are in `.cache/flow-before-metal.json`
and `.cache/flow-after-metal.json`. Both checks used the same synthetic files;
no microphone recording was captured for testing.

**Hands-free conversation** now listens after correction examples as well as
replies. A repetition with `no_clear_difference` resumes the held conversation
without another model call or a Continue click. Uncertain or unsupported sound
results stay available for the learner to review. This outcome does not certify
correct pronunciation. Hands-free stays opt-in; the microphone opens only after
audio playback ends and while the page is visible.

**Sound feedback uses the recorded audio, independently of the ASR transcript.**
[University ZIPA Luxembourgish](https://huggingface.co/pgilles/zipa-large-crctc-luxembourgish-ipapack20)
predicts IPA phones. [University MFA dictionary](https://github.com/PeterGilles/Luxembourgish_in_Montreal_Forced_Aligner)
provides reference variants. A graph alignment considers all listed variants and
accepts ordinary uvular r variation; an uncalibrated acoustic-posterior cutoff
suppresses weak substitution tips. Missing/extra phones and unlisted words do
not produce confident corrections. The recognizer never receives the expected
text. It cannot assess speech sounds outside its phone inventory reliably.

This is **experimental phonetic coaching, not a validated pronunciation grade**.
Matching phones do not prove correctness; timing is approximate, and regional
or connected-speech variants may be absent from the dictionary. Stress,
intonation, overall accent and fine vowel quality are not graded. Very short
isolated words were unreliable in synthetic checks; sentence context helped.
Targets are limited to ten dictionary words and audio to twenty seconds.
Unknown words, numbers, quiet audio and highly divergent sound sequences get
explicit limitations rather than invented corrections. No LLM invents the
phonetic evidence or assessment. Wording feedback still uses a transcript.

The ZIPA model card labels the fine-tune MIT, while its upstream `ns` base weights
are CC BY-NC-SA 4.0. Use is personal and noncommercial here; retain both notices
and clarify before redistribution. Inference source is pinned to ZIPA commit
`21e9e8aa4cc6c130cb05d836a1979886f9245302`; the included icefall files carry
Apache-2.0 notices, and the ZIPA repo also has an MIT license. The dictionary is
Apache-2.0. Weights and downloaded source remain outside Git.

The Mac adapter uses strict checkpoint loading and pure PyTorch Swoosh inference
formulas to avoid CUDA/k2. Its CTC blank is class 0, as in the published decoder
and PyTorch CTC training, despite the tokenizer's `<blk>` ID 1 metadata. It uses
the original Lhotse filterbank extractor and disables inference dropout.
Synthetic speech and model-generated Luxembourgish still need human review;
use course recordings and LOD as references.

## Install again on another Mac

Requires Python 3.12, Node/npm for the launch shortcut, and either OpenCode v2
or Ollama for conversation replies. Private lesson notes are optional.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-pronunciation.txt
.venv/bin/python download_models.py
.venv/bin/python download_models.py --pronunciation
npm run dev
```

Downloaded weights, caches, environments, and certificates are git-ignored.

## Conversation flow improvements (16 October)

Sound coaching now starts as soon as local ZIPA detects a possible difference,
even while the conversation model is still preparing its reply. You can listen
and record another attempt during that wait. The reply is held until sound
practice is finished, and any wording correction follows the sound correction.
A late reply never interrupts a recording or an example. Reset aborts both the
tutor request and the current practice request. With hands-free enabled, a repeat
with no clear mismatch can continue when the held reply becomes available.

Both free online models now use their advertised low reasoning variant when
available. In a small alternating synthetic check, GLM low took 4.11 and 23.67
seconds; its default took 19.31 and 38.46 seconds. This is a variable two-sample
comparison, not a reliable speed guarantee. Provider delay and generated language
errors remain possible. A subsequent app-endpoint check returned DeepSeek in
3.65 seconds and GLM timed out at 90.04 seconds. DeepSeek remains the default.
Results: `.cache/glm-effort-benchmark.json` and `.cache/online-low-validation.json`
(synthetic text only). The local speech model, beam size, and phonetic checks were preserved.

## Phone access

The easiest setup is a home-screen web app with this Mac as the backend. Use
[Tailscale Personal](https://tailscale.com/docs/reference/free-plans-discounts)
(free for personal use) on both devices and
[Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve)
for a private HTTPS address. Plain Wi-Fi HTTP cannot use the phone microphone.

1. Install [Tailscale](https://tailscale.com/download) on the Mac and phone. Sign
   in to the same personal account and connect both devices.
2. Stop the existing app server, then run `npm run phone` in `schwatz/`.
   The launcher detects this Mac's Tailscale hostname, permits that exact host,
   and keeps Uvicorn bound to localhost. It prints your phone address.
3. In another terminal run `tailscale serve http://127.0.0.1:8765`. Follow its
   HTTPS setup link if prompted. This serves the app within your private tailnet;
   keep the command running. If this Mac already uses Serve, inspect
   `tailscale serve status` first and choose a different HTTPS port for this app.
4. Open the printed HTTPS address on the connected phone and allow microphone
   access. On iPhone use Safari → Share → Add to Home Screen; on Android use
   Chrome's menu → Add to Home screen / Install app.

If the CLI is not on PATH, the Mac app includes it at
`/Applications/Tailscale.app/Contents/MacOS/Tailscale`; use that path instead of
`tailscale`. The launcher also detects this bundled command. You can inspect
setup without starting anything with `npm run phone -- --check`, or supply the
Mac's exact DNS name using `--hostname my-mac.tail123.ts.net`.

No Tailscale installation, login, HTTPS enablement, or service sharing is done by
the launcher. These steps have not been completed on this Mac. Do not use Funnel
or a public tunnel for this personal server. Only put your own devices/users in
the tailnet, because they can access this app without another app password.
The Mac and app must stay running; `caffeinate -i npm run phone` can prevent idle
sleep while you practise. Phone audio travels privately to the Mac for ZLS/ZIPA
analysis; Piper examples return to the phone. OpenCode receives only the selected
text context. Offline caching covers the interface; speech requires the backend.
Stop Serve with `tailscale serve http://127.0.0.1:8765 off` when finished.

## Checks

```sh
.venv/bin/python -m pip install pytest
npm test
node --check public/app.js
```

The tests cover lesson grounding, original reference availability, isolation of
vault files, input limits, same-origin protections, and waiting for a learner's
attempt. JavaScript checks cover overlapping sound/reply requests, preserving
sound evidence after a failed reply, stale-session cancellation, typed turns and
retries. Audio and conversation quality require separate end-to-end checks and
testing with real learner speech. Synthetic end-to-end checks detected the vowel
change from /əʊ/ to /eː/ in “Ech soen Brout.” and suppressed weak/ambiguous
results. This is a smoke check, not evidence of accuracy on real learners.

For a reproducible local model comparison:

```sh
.venv/bin/python benchmark_models.py qwen3.8:27b qwen3.8:27b-mlx gemma4:26b-a4b-it-qat
```

Install the named models in Ollama first. The benchmark uses six synthetic
lesson-grounded turns and writes timings and replies to `.cache/model-benchmark.json`.
It runs models sequentially, unloads each tested model before and after its run,
uses an 8192-token context and disables thinking. It does not upload recordings.
The first turn includes loading; subsequent turns change prompts and scenarios,
so their median is not an exact repeated-prompt cache measurement. Review the
actual replies against the notes: speed and valid JSON do not establish language
accuracy. Loading times also depend on the operating system's file cache.

### Comparison on this Mac — 13 October 2026

M1 Max, 64 GB unified memory, Ollama 0.32.13; all tested models fit fully on the
GPU. The same original prompts and six attempts were used for these results.
Median excludes the first loading turn and includes changes of scenario; it
excludes transcription, pronunciation inference and voice synthesis.

| Model | Median subsequent reply | Decision |
| --- | ---: | --- |
| Qwen3.8 27B Q4_K_M (existing MTP build) | 14.4 s | Keep as default |
| Qwen3.8 27B MLX / NVFP4 | 16.7 s | Faster token generation, slower prompt processing; irrelevant wording feedback in one case |
| Gemma 4 26B-A4B QAT / Q4_0 | 3.9 s | Available in Settings; German/English intrusions and malformed Luxembourgish in samples |
| Qwen3.6 35B-A3B Q4_K_M | 3.2 s | Available in Settings; subsequent check also found malformed Luxembourgish and inaccurate grammar feedback |

These are a small practical comparison, not a validated Luxembourgish ranking.
Qwen3.8 also missed the separable-verb error and invented a formal-pronoun claim.
The revised prompt avoids unnecessary tips for valid sentences in the checked
examples, but does not establish reliable grammar correction. No tested model
earned a default switch on language quality. A repeat of Qwen3.6 with the revised
prompt had a 3.4 s median; improvements to prompts and examples do not eliminate
language errors. Continue to use course evidence and LOD as reference.

The downloaded candidates remain installed for comparison. Raw replies and
timings are under `.cache/model-benchmark*.json`, excluded from Git. To reproduce
Qwen3.6 against the frozen original prompts, use `--prompt-set
original-benchmark-prompts.json` with the benchmark command.
