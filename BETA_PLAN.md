# Web beta for up to 100 invited testers

Status: proposed rollout, not a deployed public service or approved spend.
100 invited people is the cohort target; simultaneous speech capacity must be
measured. The personal Mac deployment continues separately.

## Experience and stack

Testers open an HTTPS link, enter an individual invitation code once, allow the
microphone when starting practice, and use the existing mobile web interface.
They do not configure a provider, key, model or Tailscale account. Home-screen
installation is optional. Maintain the plain JavaScript interface and FastAPI
backend. Add SQLite for invite identities, sessions and durable usage counters
on a single host; raw recordings and conversation text are not needed for quotas.

Use one dedicated, server-managed OpenRouter key with an explicit model allowlist
and spending cap. Select the model after a capped paid comparison of Luxembourgish
corrections, false corrections, translations and latency. No paid quality winner
has been established. Do not silently substitute a model after a failure.

Mac-hosted speech plus a protected Tailscale Funnel endpoint can serve the first
cohort. Funnel is bandwidth-limited and the Mac must stay awake and online. The
source code being public does not grant public access to the personal server.
Keep the personal endpoint private and publish only the isolated beta service.
Move speech to dedicated compute if measured demand exceeds this host's capacity;
no paid hosting or always-on capacity has been purchased or promised.

## Proposed starting limits

| Scope | Initial ceiling |
| --- | --- |
| Whole trial | $20 in model usage, no automatic top-ups; purchase fees additional |
| All testers together | $2/day when expanding toward 100 accounts |
| Each person | 20 model requests or $0.10/day, whichever is reached first |
| Request accounting | Conversation replies and passage translations both count |
| Each person's speech | 40 uploads/day, including retries; at most 30 seconds each |
| Pronunciation clips | At most 20 seconds and the existing supported target scope |
| Each person's active requests | One active speech submission; repeated taps cannot duplicate charges |
| Heavy speech work | Initially one analysis job running with a short, bounded queue |

These are ceilings, not guaranteed reserved allowances. The shared daily or total
budget can be exhausted before everyone reaches an individual ceiling. With a
$20 total cap and $2/day cap, the trial could consume the entire budget in ten
fully used days. Daily reset time and remaining requests must be clear to testers.
Dollar amounts are proposals for the owner to choose, not existing billing settings.

Enforce totals server-side across restarts and simultaneous requests. Reserve
estimated maximum request cost before starting generation, reconcile provider
usage afterward, and fail closed if the price, account balance or accounting
cannot be verified. Keep the provider-side key cap as an additional control.
Do not rely on browser storage or IP addresses as person-level quota enforcement.

When limits are reached, preserve the current attempt and show when practice can
resume. Non-generative listening exercises remain available. Buy Me a Coffee can
be an optional support link; donations do not promise instant access, automatically
raise limits or instantly refill OpenRouter. Start with manual credit top-ups.

## Rollout order

1. Connect the owner's provider key securely and approve the comparison budget.
   Compare explicit model versions on synthetic and consenting learner examples;
   have a fluent Luxembourgish speaker review the language outputs.
   [BETA_SETUP.md](BETA_SETUP.md) describes the prepared, synthetic-only runner
   and its required non-resetting provider key limit of US$1 or less.
2. Implement the invitation, shared-key and accounting controls above. The current
   public mode is still BYOK; it does not implement this proposed experience.
3. Prepare original, shareable A2 examples. Public mode excludes the private vault,
   so it cannot automatically reuse all course grounding from the personal demo.
   Resolve the phonetic model's upstream license ambiguity and voice notices for
   a publicly hosted, donation-supported deployment. Prefer publisher links until
   permission to mirror recordings has been established; see THIRD_PARTY.md.
4. Test with 10 invitees, then 25, then expand toward 100. Before each increase,
   measure queue wait and end-to-end response times, error rates, Mac memory/CPU
   pressure, per-person costs and unnecessary language corrections. Test five
   concurrent speaking sessions before assuming the Mac can sustain that load.
5. Publish the protected beta endpoint after the owner reviews its concrete access
   and data handling. Add a redacted feedback form and a way to revoke invitations
   and stop new model requests immediately.

## References

- OpenRouter prices and limits: https://openrouter.ai/pricing
- OpenRouter spending controls: https://openrouter.ai/blog/tutorials/team-spend-controls-setup/
- Funnel requirements: https://tailscale.com/docs/features/tailscale-funnel
- Buy Me a Coffee fees and payouts: https://help.buymeacoffee.com/en/articles/10182730-what-is-buy-me-a-coffee-and-how-does-it-work

Provider offers change. Recheck the selected models, prices, terms and deployment
permissions before launch; this document does not certify language accuracy or
interpret third-party license permissions as settled.
