# Security

Report security vulnerabilities privately at:
https://github.com/breadowners/schwatz/security/advisories/new

Describe the affected version, impact, and the smallest synthetic reproduction.
Do not put credentials, personal recordings or private notes in public issues.
If a key is exposed, revoke it with its provider. The project cannot revoke a
third-party key on your behalf. This volunteer project has no guaranteed response
time or independently audited security certification.

## Deployment scope

The current default is a personal app bound to localhost, optionally reached over
private Tailscale Serve. Sharing its source does not publish the running app.
`SPEAK_PUBLIC=1` hides private notes and host model access, but currently requires
each visitor's own provider key. It is not a complete public-service security layer.

A shared-budget beta still needs server-managed credentials, per-person access,
durable quota accounting, bounded request queues and resource monitoring. Those
controls are proposed in [BETA_PLAN.md](BETA_PLAN.md); they are not active yet.
Keep production secrets in deployment configuration, downloaded assets outside
Git, and raw request bodies and authorization headers out of logs. Model and
recording licenses remain separate from the source-code license.
