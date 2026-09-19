# Security

This demo is safe-by-design but not a production sandbox.

Production requirements:
- authenticate and authorize the MCP HTTP endpoint
- ephemeral sandbox per task
- no host Docker socket
- non-root user, seccomp/AppArmor, read-only base filesystem
- egress deny-by-default
- secrets broker with short-lived credentials
- path allowlists
- command allowlists
- dependency-install policy
- malware/secrets scanning
- prompt-injection handling for repository content
- branch protection
- signed audit events
- human approval for writes/push/PR/merge as appropriate
- never let an LLM self-authorize

Repository text is untrusted input. Comments/README files can contain prompt injection and must not override system/tool policy.
