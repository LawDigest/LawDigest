
import unittest
from unittest.mock import MagicMock, patch
from lawdigest_data.connectors.DatabaseManager import DatabaseManager

class TestDatabaseManagerLogic(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager(host="fake", username="fake", password="fake", database="fake")
        # Mock connection and cursor
        self.db_manager.connection = MagicMock()
        self.cursor = MagicMock()
        # transaction context manager mock
        # transaction() returns a generator that yields the cursor
        # We need to mock __enter__ and __exit__ for the context manager or just mock the method
        
    def test_insert_bill_info(self):
        """Test insert_bill_info calls executemany and handles proposers correctly"""
        # Data to insert
        bills_data = [
            {
                "bill_id": "BILL1",
                "bill_name": "Test Bill 1",
                "summary": "Summary 1",
                "public_proposer_ids": ["EJ001", "EJ002"],
                "rst_proposer_ids": ["EJ001"]
            },
            {
                "bill_id": "BILL2",
                "bill_name": "Test Bill 2",
                "summary": "Summary 2",
                "public_proposer_ids": [],
                "rst_proposer_ids": []
            }
        ]
        
        # Mock transaction to yield our mock cursor
        with patch.object(self.db_manager, 'transaction') as mock_transaction, patch.object(
            self.db_manager,
            "_bill_table_has_column",
            return_value=True,
        ), patch.object(
            self.db_manager,
            "_bill_table_enum_values",
            return_value={"CHAIRMAN", "CONGRESSMAN", "GOVERNMENT"},
        ):
            mock_transaction.return_value.__enter__.return_value = self.cursor
            
            # Setup mock behavior for _link_proposers SELECT
            # First call for BILL1 public proposers returns valid congressmen
            self.cursor.fetchall.side_effect = [
                # For BILL1 public_proposer_ids check
                [{"congressman_id": "EJ001", "party_id": 10}, {"congressman_id": "EJ002", "party_id": 20}],
                 # For BILL1 rst_proposer_ids check
                [{"congressman_id": "EJ001", "party_id": 10}],
            ]

            self.db_manager.insert_bill_info(bills_data)
            
            # Verify Bill Upsert
            self.assertTrue(self.cursor.executemany.called)
            # First call should be Bill upsert
            args, _ = self.cursor.executemany.call_args_list[0]
            self.assertIn("INSERT INTO Bill", args[0])
            expected_bills = [
                {
                    **bills_data[0],
                    "summary_tags": None,
                },
                {
                    **bills_data[1],
                    "summary_tags": None,
                },
            ]
            self.assertEqual(args[1], expected_bills)
            
            # Verify BillProposer Delete & Insert (for BILL1)
            # self.cursor.execute called for DELETE
            # self.cursor.executemany called for INSERT
            
            # Check delete calls
            delete_calls = [c for c in self.cursor.execute.call_args_list if "DELETE FROM" in c[0][0]]
            self.assertEqual(len(delete_calls), 2) # BillProposer, RepresentativeProposer for BILL1
            
            # Check insert calls for link proposers
            # call_args_list[0] is Bill upsert (executemany)
            # call_args_list[1] is BillProposer Insert (executemany) - wait, interspersed with execute
            
            # Let's inspect all executemany calls
            executemany_calls = self.cursor.executemany.call_args_list
            self.assertEqual(len(executemany_calls), 3) # Bill Upsert, BillProposer Insert, RepProposer Insert
            
            # Check BillProposer Insert params
            bp_insert_args = executemany_calls[1]
            self.assertIn("INSERT INTO BillProposer", bp_insert_args[0][0])
            self.assertEqual(len(bp_insert_args[0][1]), 2) # 2 proposers
            
            # Check RepProposer Insert params
            rp_insert_args = executemany_calls[2]
            self.assertIn("INSERT INTO RepresentativeProposer", rp_insert_args[0][0])
            self.assertEqual(len(rp_insert_args[0][1]), 1) # 1 proposer

    def test_insert_bill_info_omits_summary_tags_when_column_absent(self):
        bills_data = [
            {
                "bill_id": "BILL1",
                "bill_name": "Test Bill 1",
                "summary": "Summary 1",
                "summary_tags": '["태그"]',
                "public_proposer_ids": [],
                "rst_proposer_ids": [],
            }
        ]

        with patch.object(self.db_manager, "transaction") as mock_transaction, patch.object(
            self.db_manager,
            "_bill_table_has_column",
            return_value=False,
        ), patch.object(
            self.db_manager,
            "_bill_table_enum_values",
            return_value={"CHAIRMAN", "CONGRESSMAN", "GOVERNMENT"},
        ):
            mock_transaction.return_value.__enter__.return_value = self.cursor

            self.db_manager.insert_bill_info(bills_data)

            bill_query = self.cursor.executemany.call_args_list[0].args[0]
            self.assertNotIn("summary_tags", bill_query)

    def test_insert_bill_info_fails_before_upsert_when_proposer_kind_enum_is_missing(self):
        bills_data = [
            {
                "bill_id": "BILL-GOV",
                "bill_name": "정부 제출 법안",
                "summary": "정부 제출 법안 요약",
                "proposer_kind": "GOVERNMENT",
                "public_proposer_ids": [],
                "rst_proposer_ids": [],
            }
        ]

        with patch.object(self.db_manager, "transaction") as mock_transaction, patch.object(
            self.db_manager,
            "_bill_table_has_column",
            return_value=False,
        ), patch.object(
            self.db_manager,
            "_bill_table_enum_values",
            return_value={"CHAIRMAN", "CONGRESSMAN"},
        ):
            mock_transaction.return_value.__enter__.return_value = self.cursor

            with self.assertRaisesRegex(RuntimeError, "GOVERNMENT"):
                self.db_manager.insert_bill_info(bills_data)

            self.cursor.executemany.assert_not_called()

    def test_insert_bill_info_fails_before_transaction_when_summary_is_missing(self):
        bills_data = [
            {
                "bill_id": "BILL-NO-SUMMARY",
                "bill_name": "요약 없는 법안",
                "summary": " ",
                "public_proposer_ids": [],
                "rst_proposer_ids": [],
            }
        ]

        with patch.object(self.db_manager, "transaction") as mock_transaction:
            with self.assertRaisesRegex(ValueError, "Bill.summary is required"):
                self.db_manager.insert_bill_info(bills_data)

            mock_transaction.assert_not_called()
            self.cursor.executemany.assert_not_called()

    def test_link_proposers_ignores_empty_and_nan_ids(self):
        self.db_manager._link_proposers(
            self.cursor,
            "BILL-GOV",
            [None, "", " ", "nan", "NaN"],
            is_representative=False,
        )

        self.cursor.execute.assert_not_called()
        self.cursor.executemany.assert_not_called()

    def test_insert_bill_alternatives_upserts_valid_pairs(self):
        alternatives_data = [
            {"alternative_bill_id": "ALT-1", "original_bill_id": "ORG-1"},
            {"alternative_bill_id": "ALT-1", "original_bill_id": "ORG-1"},
            {"alternative_bill_id": "", "original_bill_id": "ORG-2"},
            {"alternative_bill_id": "ALT-2", "original_bill_id": None},
        ]

        with patch.object(self.db_manager, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.cursor

            inserted = self.db_manager.insert_bill_alternatives(alternatives_data)

        self.assertEqual(inserted, 1)
        self.cursor.executemany.assert_called_once()
        query, params = self.cursor.executemany.call_args.args
        self.assertIn("INSERT INTO BillAlternative", query)
        self.assertEqual(params, [("ALT-1", "ORG-1")])

    def test_fetch_bill_search_document_candidates_selects_missing_or_stale_ready_bills(self):
        with patch.object(self.db_manager, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.cursor
            self.cursor.fetchall.return_value = [{"bill_id": "BILL-1"}]

            rows = self.db_manager.fetch_bill_search_document_candidates(limit=50)

        self.assertEqual(rows, [{"bill_id": "BILL-1"}])
        query, params = self.cursor.execute.call_args.args
        self.assertIn("LEFT JOIN BillSearchDocument", query)
        self.assertIn("b.ingest_status = 'READY'", query)
        self.assertIn("bsd.bill_id IS NULL", query)
        self.assertEqual(params, (50,))

    def test_upsert_bill_search_documents_uses_replace_semantics(self):
        documents = [
            {
                "bill_id": "BILL-1",
                "bill_name_text": "법안명",
                "brief_summary_text": "짧은 요약",
                "gpt_summary_text": "AI 요약",
                "raw_summary_text": "원문 요약",
                "search_text": "법안명 짧은 요약 AI 요약 원문 요약",
                "source_modified_date": "2026-06-27 10:00:00",
            }
        ]

        with patch.object(self.db_manager, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.cursor

            count = self.db_manager.upsert_bill_search_documents(documents)

        self.assertEqual(count, 1)
        query, params = self.cursor.executemany.call_args.args
        self.assertIn("INSERT INTO BillSearchDocument", query)
        self.assertIn("ON DUPLICATE KEY UPDATE", query)
        self.assertEqual(params, documents)

    def test_update_bill_stage(self):
        """Test update_bill_stage filters duplicates and batches updates"""
        stage_data = [
            {"bill_id": "BILL1", "stage": "Temp", "status_update_date": "2023-01-01"},
            {"bill_id": "BILL2", "stage": "Pass", "status_update_date": "2023-01-02"},
            {"bill_id": "BILL3", "stage": "Rej", "status_update_date": "2023-01-03"} # Assumed not in DB
        ]
        
        with patch.object(self.db_manager, 'transaction') as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.cursor
            
            # Mock get_existing_bill_ids: BILL1, BILL2 exist, BILL3 does not
            self.db_manager.get_existing_bill_ids = MagicMock(return_value=["BILL1", "BILL2"])
            
            # Mock timeline check SELECT: BILL1 already has this stage/date
            self.cursor.fetchall.return_value = [
                {"bill_id": "BILL1", "bill_timeline_stage": "Temp", "status_update_date": "2023-01-01"}
            ]
            
            result = self.db_manager.update_bill_stage(stage_data)
            
            # Verify Results
            self.assertIn("BILL3", result["not_found_bill"]) # BILL3 not in existing_ids
            self.assertTrue(any("BILL1" in s for s in result["duplicate_bill"])) # BILL1 duplicate
            
            # Verify Update Execution
            # Should only update/insert for BILL2
            executemany_calls = self.cursor.executemany.call_args_list
            self.assertEqual(len(executemany_calls), 2) # Update Bill, Insert Timeline
            
            # Check Update Bill
            update_args = executemany_calls[0]
            self.assertIn("UPDATE Bill SET stage", update_args[0][0])
            self.assertEqual(len(update_args[0][1]), 1)
            self.assertEqual(update_args[0][1][0], ("Pass", "BILL2"))
            
            # Check Insert Timeline
            insert_args = executemany_calls[1]
            self.assertIn("INSERT INTO BillTimeline", insert_args[0][0])
            self.assertEqual(len(insert_args[0][1]), 1)
            self.assertEqual(insert_args[0][1][0][0], "BILL2")

if __name__ == '__main__':
    unittest.main()
