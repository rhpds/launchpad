# Multi-Agent Quickstart seat runtime

This chart adapts the immutable upstream Multi-Agent Quickstart source into a
Launchpad seat. It runs the orchestrator, three A2A agents, MCP server,
guardrails service, and participant UI in one pod while preserving a Service
for each protocol endpoint. Launchpad supplies model and service credentials
through a per-seat Secret and supplies ownership identity through Helm values.

The image repository and immutable digest are required at render time. The
chart never creates or serializes a Secret.
