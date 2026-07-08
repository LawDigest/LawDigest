---
title: Election And Poll Storage
topics: [concepts]
sources:
  - id: election-database
    type: file
    path: services/data/src/lawdigest_data/elections/database.py
  - id: nec-api-client
    type: file
    path: services/data/src/lawdigest_data/elections/api_client.py
  - id: election-workflow
    type: file
    path: services/data/src/lawdigest_data/elections/workflow.py
  - id: election-candidate-models
    type: file
    path: services/data/src/lawdigest_data/elections/models/candidates.py
  - id: election-code-models
    type: file
    path: services/data/src/lawdigest_data/elections/models/codes.py
  - id: candidate-collector
    type: file
    path: services/data/src/lawdigest_data/elections/collectors/candidate_collector.py
  - id: code-collector
    type: file
    path: services/data/src/lawdigest_data/elections/collectors/code_collector.py
  - id: polls-database-manager
    type: file
    path: services/data/src/lawdigest_data/connectors/PollsDatabaseManager.py
  - id: polls-workflow
    type: file
    path: services/data/src/lawdigest_data/polls/workflow.py
  - id: election-controller
    type: file
    path: services/backend/src/main/java/com/everyones/lawmaking/controller/ElectionController.java
  - id: poll-query-service
    type: file
    path: services/backend/src/main/java/com/everyones/lawmaking/service/election/poll/PollQueryService.java
---

# Election And Poll Storage

Election and poll storage in Lawdigest is a pair of data paths for local election information and public opinion survey results. Election data is collected through National Election Commission APIs into SQLAlchemy-managed tables, while poll data is crawled and parsed from NESDC survey material into runtime-created MySQL tables. The two paths are separate because official election entities and survey result tables have different source systems, ingestion rhythms, and read patterns, but they meet in the backend election API that serves selector, map, candidate, and poll views [@election-controller].

## Responsibility

The election storage path is responsible for code lists, districts, parties, jobs, education codes, candidates, winners, pledges, party policies, and election news. It uses a dedicated SQLAlchemy `Base`, engine, and session manager rather than the older `DatabaseManager` class used by bill ingestion [@election-database].

The poll storage path is responsible for survey metadata, questions, and response options. `PollsDatabaseManager` creates and writes `PollCatalog`, `PollSurvey`, `PollQuestion`, and `PollOption` with direct MySQL DDL and upsert methods [@polls-database-manager].

Both paths support dry-run operation. `ElectionWorkflowManager` writes artifact JSON and avoids DB writes unless the mode is `test` or `prod` [@election-workflow]. `PollsWorkflowManager` normalizes the shared execution mode and avoids poll upserts in `dry_run` [@polls-workflow].

This page is related to [Election API](../backend/election-api.md), [Integration Test Policy](../../guides/verification/integration-test-policy.md), and [External APIs](../../reference/integrations/external-apis.md).

## Election Storage Path

The election API client targets `http://apis.data.go.kr/9760000`, maps logical services such as code, candidate, winner, pledge, and party policy to service paths, and paginates responses until the fetched item count reaches `totalCount` [@nec-api-client]. It supports XML and JSON parsing, checks public data result codes, and retries transient HTTP failures through `HTTPAdapter` and `Retry` [@nec-api-client].

Election code models define tables such as `election_codes`, `election_districts`, `election_gusiguns`, `election_parties`, `election_jobs`, and `election_educations`, each with uniqueness constraints that match source identity fields [@election-code-models]. Candidate storage combines preliminary and confirmed candidates in `election_candidates` and stores winners in `election_winners`; both include normalized region and election-name fields for poll linkage [@election-candidate-models].

Collectors use MySQL `INSERT ... ON DUPLICATE KEY UPDATE` through SQLAlchemy's MySQL dialect. The code collector upserts election code operations by configured unique keys, and the candidate collector upserts candidates by `huboid`, `sg_id`, and `candidate_type` [@code-collector] [@candidate-collector]. Winner collection later links winner rows back to candidate rows when possible [@candidate-collector].

## Poll Storage Path

Poll storage begins with NESDC crawling. `PollsWorkflowManager` scans catalog pages, fetches target poll lists, crawls details, downloads or parses result material, and writes artifacts under `.airflow_artifacts` by default [@polls-workflow].

Parsed result sets become survey rows, question rows, and option rows. `upsert_polls_step` builds one `PollSurvey` row per result set, one `PollQuestion` row per parsed question, and normalized `PollOption` rows for each valid percentage [@polls-workflow]. Invalid option percentages are skipped rather than written [@polls-workflow].

`PollsDatabaseManager.ensure_tables` creates the poll tables at runtime if they do not exist. Survey metadata is keyed by `registration_number`; questions are unique by registration number and question number; options are replaced for a question by deleting old options and inserting the current parsed set [@polls-database-manager].

## Backend Read Boundary

The backend exposes poll data under `/v1/election/polls/overview`, `/v1/election/polls/party`, `/v1/election/polls/region`, and `/v1/election/polls/candidate` [@election-controller]. The controller delegates these endpoints to `PollQueryService`.

`PollQueryService` reads surveys by normalized election label and region label, classifies questions into party support, matchup, or candidate fit, and aggregates option percentages into overview, party, region, and candidate response shapes [@poll-query-service]. This means the storage contract is not just table presence; question text must remain classifiable and option names must be normalizable for API responses to be useful.

## Invariants

Election rows must preserve source identifiers. Candidate uniqueness depends on `huboid`, `sg_id`, and `candidate_type`; winner uniqueness depends on `huboid` and `sg_id`; election code uniqueness depends on source code fields such as `sg_id` and `sg_typecode` [@election-candidate-models] [@election-code-models].

Poll survey identity is `registration_number`, and question identity is the pair of registration number and question number. Replacing options by `question_id` makes each question's options represent the most recent parsed result set rather than an append-only history [@polls-database-manager].

The election and poll paths share normalized join fields but do not share one storage framework. Election collectors use SQLAlchemy sessions; poll writes extend the pymysql-based `DatabaseManager` path [@election-database] [@polls-database-manager].

## Failure Modes

External API failures can stop or reduce election collection. `NecApiClient` raises request errors or `NecApiError` when response codes are not successful [@nec-api-client]. Some workflow dry-run steps catch missing-data cases, such as no winner data before an election, and record an artifact note instead of writing rows [@election-workflow].

Poll parsing can produce zero result sets if PDF formats, pollster registry behavior, or download state do not match parser expectations. The poll parser step logs this condition and still returns an artifact result with zero parsed records [@polls-workflow].

Poll API responses can be empty even when survey rows exist if question classification or normalization fails. `PollQueryService` filters questions by classifier output before building party or candidate snapshots [@poll-query-service].

Schema drift is also a practical risk. The poll tables are created by runtime DDL in the data service, while backend JPA entities read the same tables. Changes to poll DDL must be checked against the backend entities and repositories before being treated as safe [@polls-database-manager] [@poll-query-service].
