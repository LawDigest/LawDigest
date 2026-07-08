---
title: Getting Started
topics: [concepts]
sources:
  - id: coverage-map
    type: file
    path: almanac/coverage-map.md
  - id: readme
    type: file
    path: README.md
  - id: product
    type: file
    path: PRODUCT.md
  - id: agents
    type: file
    path: AGENTS.md
  - id: makefile
    type: file
    path: Makefile
---

# Getting Started

Getting Started is the front door for future Lawdigest agents and maintainers. It exists to turn the repository from a large monorepo into a navigable civic information system: first understand the product purpose, then identify the service boundary, then choose the smallest verified workflow for the task. The coverage map assigns this page that role explicitly, with planned links to product, data, web, verification, and deployment topics [@coverage-map].

## Repository Subject

Lawdigest, also named "모두의입법" in the repository README, is a service that makes complex National Assembly bills easier to read through AI-assisted summaries and familiar feed-style interfaces [@readme]. The product model is broader than a single summary tool: it includes bill feeds, bill detail pages, legislator and party profiles, search, following, timelines, notifications, and a bill-grounded RAG chatbot [@readme].

The product document defines the main users as citizens and voters who want to understand how legislative and election information affects their lives. It also states that high-engagement political users, journalists, civic organizations, and monitoring practitioners should be able to use the same product at deeper levels [@product].

## Main Service Boundaries

The repository is organized around four primary runtime surfaces. `services/web` is the Next.js frontend that renders the bill browser, detail pages, search, following, and profile flows [@readme]. `services/backend` is the Spring Boot API server for bill, legislator, party, and user domains, including OAuth2 login, JWT authentication, and Redis caching [@readme]. `services/data` collects, transforms, loads, and synchronizes National Assembly source data through the local `lawdigest-pipeline` runtime [@readme]. `services/ai` contains the bill summary/report processor and the RAG path that combines vector search with language-model responses [@readme].

These boundaries matter because most tasks should start by locating the surface that owns the behavior. A feed rendering issue usually begins in `services/web`; a REST contract issue begins in `services/backend`; a missing or stale bill state begins in `services/data`; and a generated report issue begins in `services/ai`.

## Product Path

Use [Lawdigest Product Model](concepts/product/lawdigest-product-model.md) when the task asks what the product is, what user value it serves, or why a feature belongs in the system. The product document says the successful experience starts from easy summaries and moves naturally into grounded detail, without pushing users toward a political direction or overwhelming them with institutional complexity [@product].

Use [Source Backed User Trust](concepts/product/source-backed-user-trust.md) when the task touches generated copy, report facts, uncertainty, legal terminology, or user-facing claims. Lawdigest treats trust as product behavior: summaries, AI output, feeds, and search results should expose source, freshness, processing state, and uncertainty when needed [@product].

## Data And Runtime Path

Use `services/data` when the task concerns bill ingest, status sync, search document rebuilds, legal-term dictionary sync, or pipeline run records. The README says the current standard execution path is not Airflow, but the local `lawdigest-pipeline` runtime [@readme]. It lists the principal commands as `bill-ingest`, `bill-status-sync`, `ai-summary`, and legacy batch submit/ingest fallbacks [@readme].

Use planned page `architecture/data/pipeline-runtime` when a task needs the deeper runtime model. Use planned page `guides/verification/local-verification-surface` before claiming a local change is complete.

## Web And API Path

Use planned page `architecture/web/frontend-api-boundary` when the task involves how the Next.js frontend talks to the Spring Boot backend. The README architecture diagram shows browser traffic flowing through `services/web`, then REST calls from the web frontend to the backend API, and then backend access to MySQL and Redis [@readme].

Use planned page `guides/deployment/web-deployment` before any web deploy work. The project agent instructions require checking the web deployment environment document before deployment and direct test deployment through the repository deploy script rather than manual PM2 or nginx changes [@agents].

## Work Start Checklist

Start by restating the user's intent and asking about unclear instructions before modifying files. The project instructions require that intent statement, explicit clarification for uncertain work, and branch naming in the `{tag}/{branch name}/{agent name}` form [@agents].

Before editing, list the named targets, inspect repository documentation, and check the code or runtime surface that owns the behavior. The project instructions warn against guessing from stale documents and require documented project material to be used while remembering that old documents can drift [@agents].

For local verification, use the repository commands instead of inventing task-specific substitutes. The Makefile exposes standard targets for web build and lint, backend build and test, data test and lint, and deployment entrypoints [@makefile].

## Verification Surface

The smallest verification should match the changed surface. Web changes normally begin with `make lint-web` or `make build-web`; backend behavior with `make test-backend`; data pipeline code with `make lint-data` and `make test-data` [@makefile]. Deployment work uses the documented deploy scripts and environment rules rather than direct service mutation [@agents].

For codealmanac pages, the local wiki itself is part of the verification surface. A documentation change should pass `codealmanac validate` and `codealmanac health`, because the wiki README defines normal Markdown links between pages and file evidence in `sources:` as part of the expected page structure [@coverage-map].

## Recovery

If evidence conflicts, prefer current code and runtime contracts over older prose. If the conflict affects the implementation direction, stop and ask the user before writing. If a patch fails, the project instructions require checking the path, current worktree, and latest file contents rather than repeating a large failed patch [@agents].

If a task reaches deployment or production operations, do not rely on a plausible local conclusion. The project deployment rules require using the repository deployment scripts and their environment-specific documents, and the local verification pages should be consulted before declaring the task complete [@agents].
