---
title: Agent Workflow
topics: [concepts]
sources:
  - id: coverage-map
    type: file
    path: almanac/coverage-map.md
  - id: agents
    type: file
    path: AGENTS.md
  - id: rtk
    type: file
    path: ../../../.codex/RTK.md
  - id: subagent-harness
    type: file
    path: ../../../.codex/subagent-harness.md
---

# Agent Workflow

Agent Workflow is the Lawdigest guide for starting, executing, verifying, and closing repository work without losing source-of-truth fidelity. It exists because this repository combines product documentation, application code, local runtime scripts, deployment state, and agent-specific operating rules. The coverage map assigns this guide to branch, worktree, safety, lint, commit, push, PR, and cleanup expectations [@coverage-map].

## When To Use This Guide

Use this guide at the start of any Lawdigest task that can change repository files, inspect runtime state, deploy a service, or make a user-visible claim about current behavior. Use [Local Source Of Truth](../../concepts/operations/local-source-of-truth.md) beside it when the task depends on active scripts, runtime paths, database state, or live health checks.

For pure reading tasks, the same start and evidence rules still apply, but branch, lint, commit, and push steps may not be needed. The project instructions say branches and worktrees are created when code writing begins, not during planning or documentation-only analysis that does not change code [@agents].

## Start

First, write what you understand the user to be asking. The project instructions require an intent statement before work begins [@agents]. If the instruction is unclear, ask directly before proceeding and present up to three likely interpretations [@agents].

Second, decide whether the work needs a branch or worktree. The project instructions require a branch at the start of code-writing work and require asking whether the user wants a separate worktree [@agents]. If the user requests a worktree, create it under `.worktrees/` and do the work there; do not let multiple agents edit the same working directory at the same time [@agents].

Third, list the named targets and inspect the repository sources that own them. The project instructions require documented project material to be used and warn against proceeding from guesswork when documents may be stale [@agents].

## Research

Prefer repository evidence before conclusions. For structural code questions, follow the local codegraph guidance when it is available; for literal text and file discovery, use fast repository search. The project instructions also require debugging to use real logs and real data, not only logic inspection [@agents].

Use `rtk` before shell commands in this environment. The RTK rule says shell commands should be prefixed with `rtk`, and its examples include git, test, build, and package commands [@rtk].

For broad read-heavy tasks, consider parallel subagents. The subagent harness says independent investigation, verification, log analysis, document review, or test-failure classification should be considered for parallel subagents; it also says subagents are filters for large reads and should return compressed evidence to the main agent [@subagent-harness].

## Plan

Before editing, name the files that will change and the files that will not change. Keep the plan tied to the user's requested surface. The project instructions require using small patches, checking paths before patching in worktrees, and avoiding repeated large patch attempts after failure [@agents].

For Lawdigest almanac work, planned links should follow the coverage map. The coverage map lists this guide's planned links as `concepts/operations/local-source-of-truth`, `guides/verification/local-verification-surface`, and `reference/operations/command-cheatsheet` [@coverage-map].

## Implement

Make surgical changes. Do not refactor nearby code, clean unrelated files, edit logs, or touch runtime state unless the user requested that scope. The project instructions require using the project documents, avoiding assumption, and keeping destructive work behind explicit user approval [@agents].

When editing inside a worktree, verify the current directory and target file before applying a patch. If `apply_patch` fails repeatedly, stop repeating the same patch and inspect the path, worktree, and latest file contents [@agents].

## Verify

Run the verification command that matches the changed surface. The completion rule says code work must run lint before branch commit and push [@agents]. For documentation-only almanac work, the relevant verification is `codealmanac validate` and `codealmanac health`; for web, backend, data, or AI work, use the matching local commands and any live checks required by the task.

When deployment is involved, follow the deploy documents before touching service state. The project instructions require reading the web deployment environment document before web deployment and using the environment-specific deploy guide for production, test, or development web [@agents].

## Recover

If evidence conflicts, pause and explain which source is current and why. If the conflict changes the implementation path, ask the user before proceeding. If runtime behavior disagrees with local code, inspect the active runtime path, service process, container, or database record before declaring the code wrong.

If a merge conflict occurs, the project instructions require explaining the conflicting content and offering three handling options [@agents]. If a PR is merged into `main`, remove the dedicated worktree and delete the local and remote branches used for the task [@agents].

## Close

After code work, run lint, commit, and push the branch. Commit messages use `{tag}: {message}`, with the tag in English and the message in Korean [@agents]. If the work completes a feature implementation, ask whether to create a PR, and write any GitHub issue or PR title and body in Korean [@agents].

The completion report should state what changed, what evidence was used, what verification ran, and what remains. The project instructions also require five natural follow-up suggestions after the work is complete [@agents].
