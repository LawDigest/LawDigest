---
title: Source Backed User Trust
topics: [concepts]
sources:
  - id: coverage-map
    type: file
    path: almanac/coverage-map.md
  - id: product
    type: file
    path: PRODUCT.md
  - id: bill-report-code
    type: file
    path: services/ai/src/lawdigest_ai/processor/agentic_bill_report.py
  - id: bill-report-doc
    type: file
    path: docs/ai/bill-report-agent-pipeline.md
  - id: safe-summary-html
    type: file
    path: services/web/components/Bill/BillList/Bill/SafeBillSummaryHtml.tsx
---

# Source Backed User Trust

Source Backed User Trust is the Lawdigest mental model for protecting users from invented or overconfident civic information. It exists because the product translates complex legislation into simpler language, and that translation is only useful if users can trust which facts came from source data, which facts were generated, and where uncertainty remains. The coverage map defines this page as the concept for source-backed data, explicit uncertainty, and no invented user-facing facts [@coverage-map].

## Definition

Source-backed trust means that user-facing explanations should be grounded in repository-controlled inputs, official or stored source records, and explicit validation rules. The product document says Lawdigest must expose source, freshness, processing state, and uncertainty when summaries, AI results, feeds, or search results need them [@product].

This model is especially important for generated bill reports. The latest AI report code describes the report writer as a user-facing legislative writer that must use only the deterministic evidence packet supplied in the prompt and must not call additional tools, run web searches, or execute shell commands [@bill-report-code].

## Why It Exists

Lawdigest simplifies legal and political information for citizens. Simplification creates risk: a concise summary can hide uncertainty, a generated explanation can sound more certain than the evidence, and a UI can imply that a stale status is current. The product document therefore treats trust as product behavior, not a separate audit step [@product].

The AI report pipeline extends an older short-summary flow into deeper reports about individual bills. Its documentation states that the goal is to explain what the bill changes, avoid collapsing compound amendments into one issue, and leave generation and usage metadata in a manifest [@bill-report-doc].

## Evidence Packet Rule

The current report code builds a deterministic evidence packet before asking the report writer to generate text. The packet includes the normalized DB bill payload, Open Assembly detail and summary records, bill text fields, current law lookups, committee material rows, cost estimate evidence, legal-term context, and prefetch errors [@bill-report-code].

The prompt builder then embeds that packet and instructs the writer to use only the provided evidence for factual claims [@bill-report-code]. If evidence is empty or prefetch errors exist, the report skill says not to invent missing support; the writer must stay within the bill basics and stored source summary instead [@bill-report-code].

## User-Facing Report Contract

The report contract separates user content from internal process. The report skill requires the final output to be a bill report, not investigation logs, and it forbids internal tool names, tool calls, research notes, and operator improvement suggestions in the body [@bill-report-code]. The validator enforces this by rejecting reports that leak internal investigation language, tool names, function-like strings, or meta labels such as "원문 요약:" and "용어 설명:" [@bill-report-code].

The pipeline also separates stable explanation from volatile status. The AI pipeline documentation says current review stage, result, vote results, view count, and scrap count are not fixed into AI text; the frontend and API display those values from current data instead [@bill-report-doc].

## Legal Term Trust

Legal-term explanations are constrained to known context. The report skill says tooltip candidates and meanings must come from each evidence packet's `legal_terms.context`, including law-term API results or the maintained legal and administrative glossary, and the writer must not invent new definitions [@bill-report-code].

The frontend rendering contract supports that rule by parsing `{{term:definition}}` tokens into interactive tooltip buttons with accessible labels and a viewport-constrained tooltip [@safe-summary-html]. This connects generation, validation, and rendering: generated syntax becomes a specific UI behavior rather than loose Markdown.

## Validation And Failure

Trust is enforced through validation before persistence. The report validator requires core sections such as `## 쉬운 요약` and `## 주요 내용`, rejects leaked internal process expressions, checks tooltip syntax, and rejects repeated or malformed easy-explanation patterns [@bill-report-code].

The pipeline documentation states that failed reports are recorded as failed manifest items, and `--stop-on-error` can stop execution immediately [@bill-report-doc]. In non-dry-run modes, only successful items update the DB summary fields, while dry runs produce files and manifests for inspection first [@bill-report-doc].

## Connected Pages

Use planned page `concepts/ai/evidence-first-bill-reporting` for the AI-specific version of this model. Use planned page `architecture/web/bill-report-rendering-contract` for the frontend Markdown and tooltip renderer. Use planned page `decisions/product/trustworthy-civic-copy` when deciding how much uncertainty, source context, or plain-language explanation belongs in visible copy.
