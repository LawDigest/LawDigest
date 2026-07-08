---
title: Bill Search Document
topics: [concepts]
sources:
  - id: split-review
    type: file
    path: docs/data/bill-summary-search-split-review.md
  - id: search-document-migration
    type: file
    path: infra/db/migrations/20260627_create_bill_search_document.sql
  - id: search-document-builder
    type: file
    path: services/data/src/lawdigest_data/bills/search_document.py
  - id: database-manager
    type: file
    path: services/data/src/lawdigest_data/connectors/DatabaseManager.py
  - id: workflow-manager
    type: file
    path: services/data/src/lawdigest_data/core/WorkFlowManager.py
  - id: backend-bill-repository
    type: file
    path: services/backend/src/main/java/com/everyones/lawmaking/repository/BillRepository.java
---

# Bill Search Document

Bill Search Document is the Lawdigest data structure that separates user-facing bill search text from the canonical `Bill` row. It exists because `Bill.summary` originally served both as source text and as a FULLTEXT search field, which made source-data constraints and search-index maintenance affect the same hot table [@split-review]. The current design stores rebuildable search material in `BillSearchDocument`, while `Bill` remains the source of bill identity, lifecycle state, and summary completeness.

## Responsibility

`BillSearchDocument` is responsible for holding text that can be searched, rebuilt, and discarded without changing the canonical bill record. The table contains the bill id, field-level text copies, a combined `search_text`, the source modification timestamp, and the rebuild timestamp [@search-document-migration].

The document builder constructs `search_text` from bill name, brief summary, AI summary, and raw summary. It intentionally repeats the bill name three times and the brief summary twice before appending the AI and raw summaries, giving title and short-summary terms more weight in a single FULLTEXT field [@search-document-builder].

This page is related to [Bill Data Quality States](../../concepts/data/bill-data-quality-states.md), [Rebuild Bill Search Documents](../../guides/data/rebuild-bill-search-documents.md), and [Bill Schema And Migrations](../../reference/data/bill-schema-and-migrations.md).

## Boundaries

The canonical boundary is `Bill`. `Bill.summary` remains source data, and `Bill.ingest_status` controls whether a bill is eligible for search-document rebuild [@database-manager]. `BillSearchDocument` does not decide whether a bill is complete; it mirrors eligible bill text into a search-optimized table.

The backend search boundary is `BillRepository.findBillByKeyword`. That query searches `BillSearchDocument.search_text`, joins back to `Bill`, and filters to `b.ingest_status = 'READY'` before returning bill ids [@backend-bill-repository]. This keeps search retrieval aligned with the feed visibility rule that incomplete bills should not appear as normal ready results.

The rebuild boundary is the data pipeline, not the Spring backend. `WorkFlowManager.rebuild_bill_search_documents` fetches candidates, builds documents, and writes them unless the current mode is `dry_run` [@workflow-manager].

## Flow

The rebuild flow starts by selecting candidate bills from `Bill`. `DatabaseManager.fetch_bill_search_document_candidates` joins `Bill` to `BillSearchDocument` and selects rows whose ingest status is `READY`, whose summary is present, and whose search document is either missing or older than the bill source timestamp [@database-manager].

Those rows are passed to `build_bill_search_documents`, which normalizes whitespace, drops rows without a bill id, and emits a document dictionary matching the table columns [@search-document-builder]. In non-dry-run modes, `DatabaseManager.upsert_bill_search_documents` inserts the documents and updates all copied text fields, `search_text`, `source_modified_date`, and `rebuilt_date` on duplicate key [@database-manager].

The table has a primary key on `bill_id`, a FULLTEXT index on `search_text`, an index on `source_modified_date`, and a foreign key to `Bill` with `ON DELETE CASCADE` [@search-document-migration]. That means document identity is one-to-one with the bill, search is optimized on the derived field, and deleted bills remove their derived search document.

## Invariants

Only READY bills with a non-empty raw summary should be rebuilt into search documents. The candidate query enforces both the `READY` status and `summary IS NOT NULL` / non-empty checks [@database-manager].

`search_text` is derived, not user-authored. Its contents should be regenerated from the current bill row rather than manually edited. The builder returns text copies for individual source fields and the combined weighted field from the same input row [@search-document-builder].

The rebuild process is idempotent for a given bill. Re-running it updates the same primary-key row through `ON DUPLICATE KEY UPDATE` rather than creating duplicate documents [@database-manager].

## Failure Modes

A missing `BillSearchDocument` row makes a READY bill absent from keyword search until the rebuild job catches it. The candidate selector is designed to find this condition by testing `bsd.bill_id IS NULL` [@database-manager].

A stale document can rank or match on old text. The selector treats a document as stale when the bill's `COALESCE(modified_date, created_date)` is newer than `BillSearchDocument.source_modified_date` [@database-manager].

A failed rebuild does not corrupt canonical bill rows because the rebuild writes a separate table. The original split review explicitly chose this separation so failed search-document work would not damage `Bill` source data [@split-review].

The remaining operational risk is query drift: backend search must continue to use `BillSearchDocument.search_text` and must continue joining to `Bill` for READY filtering. If search is changed, verify both the derived document table and the `Bill` visibility filter together [@backend-bill-repository].
