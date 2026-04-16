# 법안 적재 품질 및 status sync 점검 쿼리

> 작성일: 2026-04-16
> 관련 이슈: #63
> 관련 설계: `2026-04-16-bill-status-sync-lifecycle-vote-refactor.md`

## 1. Bill ingest 상태 분포

```sql
SELECT ingest_status, COUNT(*) AS bill_count
FROM Bill
GROUP BY ingest_status
ORDER BY bill_count DESC;
```

## 2. 최근 발의일 갱신 확인

```sql
SELECT MAX(propose_date) AS latest_propose_date,
       COUNT(*) AS total_bills
FROM Bill;
```

```sql
SELECT bill_id, bill_name, propose_date, stage, committee
FROM Bill
ORDER BY propose_date DESC
LIMIT 30;
```

## 3. 핵심 컬럼 결측 점검

```sql
SELECT
  SUM(CASE WHEN summary IS NULL OR summary = '' THEN 1 ELSE 0 END) AS summary_missing,
  SUM(CASE WHEN brief_summary IS NULL OR brief_summary = '' THEN 1 ELSE 0 END) AS brief_summary_missing,
  SUM(CASE WHEN proposers IS NULL OR proposers = '' THEN 1 ELSE 0 END) AS proposers_missing,
  SUM(CASE WHEN bill_pdf_url IS NULL OR bill_pdf_url = '' THEN 1 ELSE 0 END) AS bill_pdf_missing
FROM Bill;
```

```sql
SELECT bill_id, bill_name, propose_date, proposer_kind, proposers, stage
FROM Bill
WHERE summary IS NULL OR summary = ''
   OR brief_summary IS NULL OR brief_summary = ''
   OR proposers IS NULL OR proposers = ''
ORDER BY propose_date DESC
LIMIT 100;
```

## 4. lifecycle checkpoint 점검

```sql
SELECT source_name,
       assembly_number,
       last_reference_date,
       metadata,
       created_date,
       modified_date
FROM IngestCheckpoint
WHERE source_name IN ('bill_ingest', 'bill_discovery', 'bill_status_lifecycle')
ORDER BY source_name, assembly_number;
```

## 5. vote checkpoint 점검

```sql
SELECT source_name,
       assembly_number,
       last_reference_date,
       metadata,
       created_date,
       modified_date
FROM IngestCheckpoint
WHERE source_name IN ('bill_status_vote')
ORDER BY source_name, assembly_number;
```

## 6. 최근 lifecycle 반영 여부

```sql
SELECT status_update_date,
       COUNT(*) AS timeline_count
FROM BillTimeline
GROUP BY status_update_date
ORDER BY status_update_date DESC
LIMIT 14;
```

```sql
SELECT bill_id,
       bill_timeline_stage,
       bill_timeline_committee,
       status_update_date,
       bill_result
FROM BillTimeline
ORDER BY status_update_date DESC, modified_date DESC
LIMIT 50;
```

## 7. 최근 vote 반영 여부

```sql
SELECT COUNT(*) AS vote_record_count FROM VoteRecord;
SELECT COUNT(*) AS vote_party_count FROM VoteParty;
```

```sql
SELECT vr.bill_id,
       vr.total_vote_count,
       vr.votes_for_count,
       vr.votes_againt_count,
       vr.abstention_count,
       b.bill_name,
       b.stage,
       b.bill_result
FROM VoteRecord vr
JOIN Bill b ON b.bill_id = vr.bill_id
ORDER BY vr.modified_date DESC
LIMIT 50;
```

## 8. 단계/결과 projection 이상 징후

```sql
SELECT stage, bill_result, COUNT(*) AS bill_count
FROM Bill
GROUP BY stage, bill_result
ORDER BY bill_count DESC, stage;
```

```sql
SELECT bill_id, bill_name, stage, bill_result, committee, modified_date
FROM Bill
WHERE (stage = '본회의 심의' AND (bill_result IS NULL OR bill_result = ''))
   OR (stage IN ('위원회 심사', '체계자구 심사') AND (committee IS NULL OR committee = ''))
ORDER BY modified_date DESC
LIMIT 100;
```

## 9. 발의자 링크 무결성 참고 점검

```sql
SELECT COUNT(*) AS representative_proposer_rows FROM RepresentativeProposer;
SELECT COUNT(*) AS bill_proposer_rows FROM BillProposer;
```

```sql
SELECT b.bill_id, b.bill_name, b.propose_date
FROM Bill b
LEFT JOIN RepresentativeProposer rp ON rp.bill_id = b.bill_id
WHERE b.proposer_kind = 'CONGRESSMAN'
  AND rp.bill_id IS NULL
ORDER BY b.propose_date DESC
LIMIT 100;
```
