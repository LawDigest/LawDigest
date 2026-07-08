---
title: Lawdigest Product Model
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
---

# Lawdigest Product Model

The Lawdigest product model is the repo-specific mental model for a neutral civic product that turns legislative and election data into readable user journeys. It exists because the repository contains several technical systems, but their shared purpose is product trust: users should be able to begin with an easy explanation and continue into source-grounded detail, comparison, monitoring, and search. The coverage map defines this page as the concept that explains Lawdigest as feeds, summaries, profiles, timelines, and search built around understandable civic information [@coverage-map].

## Definition

Lawdigest is a Korean legislative and political information product. The product document states that it helps users understand, track, and compare legislative and political information by turning complex bills, legislator activity, party information, and election signals into feeds, summaries, timelines, profiles, and search flows [@product].

The README describes the public-facing value in narrower bill terms: National Assembly bills arrive in large numbers, and the service uses AI to extract the core points so users can see what a bill may mean for their lives without reading long legal originals first [@readme].

## Users

The core users are ordinary citizens and voters who want to understand the effect of legislation and election information on their lives [@product]. The model also includes high-engagement political users, journalists, civic organizations, and legislative monitoring practitioners, because the same data should support deeper exploration after the first quick read [@product].

This produces the repository's "easy to learn, hard to master" shape. A new user needs a readable entry point. A power user needs bill records, legislator and party context, election data, procedural stages, and source-backed details without leaving the product model [@product].

## Product Surfaces

The main user-facing surfaces are the feed, bill detail, legislator and party profile, search, following, my page, notifications, and timelines. The README lists AI bill summaries, tag classification, legislator and party following, bill timeline visualization, likes and notifications, and a bill-based RAG chatbot as major features [@readme].

These surfaces are not independent products. They are different entry points into the same civic object graph: bills, proposers, parties, users, timelines, summaries, reports, and external source records. A user can scan a feed, open a detail page, follow an actor, monitor a process stage, and search related issues because the product model treats understanding and tracking as one experience.

## System Shape

The system is split into frontend, backend, AI, data, and storage responsibilities. The README architecture places the browser in front of `services/web`, REST calls from `services/web` to `services/backend`, backend persistence in MySQL and Redis, AI processing in `services/ai`, data collection in `services/data`, and external bill data from the National Assembly Open API [@readme].

The local pipeline is part of the product model, not only an operations detail. The README states that the current standard data path is the local `lawdigest-pipeline` runtime, which coordinates bill ingest, bill status sync, AI summary generation, and legacy batch fallback commands [@readme].

## Information Progression

The ideal Lawdigest journey moves from a simple statement to verifiable context. The product document says a successful experience begins with easy summaries and then naturally moves into grounded detail; users should not be lost, politically steered, or overwhelmed by institutional complexity [@product].

This is why the product model favors progressive disclosure. Feed cards and summaries answer what the bill is about. Detail pages and timelines show where it is in the process. Profiles, search, and following let users compare actors and issues. AI reports and RAG functions add explanation, but only inside the trust rules described in [Source Backed User Trust](source-backed-user-trust.md).

## Neutral Civic Framing

Neutrality is a visible product requirement, not only an editorial preference. The product document says political colors, party information, rankings, and emphasis should be treated as information rather than persuasion [@product]. It also says the product should not feel like a government portal, politically biased community, or overly SaaS-like dashboard [@product].

The model therefore rejects features that turn civic information into partisan direction or decorative metrics. UI, copy, ranking, and generated text should help users compare and understand, while keeping the path back to source context visible.

## Connected Pages

Use planned page `architecture/web/bill-feed-and-discovery` to understand the feed and discovery implementation. Use planned page `architecture/ai/agentic-bill-report` when the product question becomes an AI report pipeline question. Use planned page `decisions/product/trustworthy-civic-copy` when a copy decision needs to preserve neutrality, plain language, and source-backed confidence.
