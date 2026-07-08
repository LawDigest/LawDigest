---
title: Local Source Of Truth
topics: [concepts]
sources:
  - id: coverage-map
    type: file
    path: almanac/coverage-map.md
  - id: agents
    type: file
    path: AGENTS.md
  - id: web-env
    type: file
    path: deploy/WEB_DEPLOY_ENVIRONMENTS.md
  - id: deploy-ops
    type: file
    path: deploy/DEPLOY_OPERATIONS.md
---

# Local Source Of Truth

Local Source Of Truth is the Lawdigest operations model that treats repository scripts, checked-in contracts, server-local runtime paths, database state, and direct health checks as the evidence for work. It exists because Lawdigest has multiple deploy targets, persistent services, data pipelines, and historical documents that can drift. The coverage map defines this concept as the habit of trusting local scripts, runtime paths, DB contracts, and live checks over stale docs or assumed external workflows [@coverage-map].

## Definition

The model is simple: before changing behavior, identify the file, script, runtime path, or data contract that currently owns that behavior. The project agent instructions require agents to use documented project material, but also warn that legacy documents may be out of date [@agents]. They also require debugging to use real logs and real data rather than only reading logic and guessing [@agents].

Local Source Of Truth does not mean every local file is equally authoritative. Current code, active deploy scripts, runtime symlinks, database records, PM2 or Docker state, and live HTTP checks can outrank older prose when they conflict. If the conflict changes the work direction, the correct action is to explain the conflict and ask before proceeding.

## Why It Exists

Lawdigest has separate web, backend, data, and AI surfaces. A change can appear complete in one surface while the actual user-facing system still runs a different release or reads different data. The deployment operations guide states that deployment is performed from the server's local shell and that scripts read the server's `.env` files for frontend and backend environments [@deploy-ops].

The web deployment environment document defines domain-specific rules: production web uses `main`, test web uses `dev`, and development web uses the selected git ref in `next dev` mode [@web-env]. These rules make a branch, script, runtime path, and domain together the source of truth for a deployment question.

## Repository Scripts

Repository scripts encode operational intent. For test web deployment, the project instructions explicitly forbid arbitrary PM2 or nginx changes and require `deploy/deploy-test-web.sh <target-worktree>` [@agents]. The web environment document lists the production, test, and development web deployment scripts and states that web deploys are run from the local shell through those scripts [@web-env].

The deployment operations guide also records backend deployment as a staged container replacement: the production backend wrapper starts a staging container, promotes it only after health checks pass, and restores the previous live container if the live health check fails [@deploy-ops].

## Runtime Paths

Runtime paths are part of the source of truth because they identify what is actually serving traffic. The deployment operations guide states that test web is based on `.runtime/test-web/current`, development web on `.runtime/dev-web/current`, and production API traffic on the live container behind `api.lawdigest.kr` [@deploy-ops].

For web environments, this means a commit hash alone is not enough evidence. A maintainer must know which worktree or runtime symlink the script deployed, which PM2 process is serving it, and which domain was checked after deployment.

## Live Checks

Live checks close the loop. The deployment operations guide lists `pm2 list` and HTTP header checks for production, test, and development web domains, plus Docker, container environment, localhost, and public API checks for backend verification [@deploy-ops].

This model also applies to product data. If a bill looks wrong in the UI, the reliable path is to trace stored DB fields, API responses, and frontend rendering rather than patching visible copy from assumption. If an AI report looks wrong, the reliable path is to inspect the generated report, manifest, evidence packet, and DB fields before deciding whether generation, validation, persistence, or rendering owns the issue.

## Boundaries

Local Source Of Truth is not permission to mutate live state casually. The project safety instructions prohibit destructive work such as database deletion, volume reset, database purge, or container deletion without user approval. The same instructions require branch and worktree discipline before code changes and preserving separate agent workspaces when worktrees are requested [@agents].

The model also does not replace documentation. Instead, documentation should point back to the source files and scripts that decide current behavior. This almanac page therefore links to planned pages `architecture/deployment/web-release-runtime`, `architecture/deployment/backend-docker-rollout`, and `guides/verification/local-verification-surface` for deeper operational detail.

## Connected Pages

Use [Agent Workflow](../../guides/operations/agent-workflow.md) when the local-source-of-truth question becomes an agent execution question. Use planned page `guides/verification/local-verification-surface` when deciding what command or live check proves a change. Use planned deployment architecture pages when a runtime path, release directory, or container rollout is the center of the task.
