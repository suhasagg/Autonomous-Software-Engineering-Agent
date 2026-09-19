# Architecture

## Control plane vs action plane
Python owns probabilistic reasoning. Java owns deterministic filesystem/build operations.

## Bounded autonomy
The repair loop has a hard maximum. Production should also cap tokens, wall-clock time, tool calls and changed files.

## Repository isolation
Each task receives its own workspace. Production should use an ephemeral container/VM per task with CPU, memory, process, network and filesystem limits.

## Build execution
The agent cannot provide arbitrary shell commands. The action plane detects supported build files and selects an allowlisted command.

## Ambiguous actions
Writes should use idempotency/version checks in production. Git commit SHA should be pinned before edits to avoid modifying a moving base.

## PR creation
Production flow: clone -> branch -> patch -> tests -> static/security scans -> human policy gate -> push -> PR. Keep merge authority separate from the coding agent.
