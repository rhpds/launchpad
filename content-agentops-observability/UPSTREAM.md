# AgentOps Showroom provenance

This Antora component was adapted from
[`rhpds/agentops-intel-showroom`](https://github.com/rhpds/agentops-intel-showroom)
at immutable revision `f1881c61de55ebf5640c27e76469f4efe458edaf`.

## Launchpad adaptations

- Replaced the mutable Showroom UI bundle with the PatternFly 6 release.
- Replaced the shared RHDP username/password and fixed `wksp-user1` project
  with Launchpad participant SSO and the generated seat namespace.
- Replaced the fixed Qwen/Gaudi narrative with the Arena
  `granite-3.2-8b-tools` model contract and evidence-gated scale language.
- Pinned application and pipeline references to
  `1e50e51c334c1b6ed854d81a3f28fd324792f481`.
- Aligned Secret, Grafana, and health-check instructions with the
  namespace-scoped Launchpad AgentOps seat chart.

The original screenshots are retained to preserve the guided workshop. They
must be refreshed wherever Arena's certified UI differs materially from the
upstream RHDP experience.
