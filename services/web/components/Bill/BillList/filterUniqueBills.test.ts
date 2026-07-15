import { describe, expect, it } from 'vitest';
import { BillResponse } from '@/types';
import { filterUniqueBills } from './filterUniqueBills';

function createBill(id: string, name = id): BillResponse {
  return {
    bill_info_dto: {
      bill_id: id,
      bill_name: name,
      propose_date: '2026-05-18',
      summary: '',
      gpt_summary: '',
      view_count: 0,
      bill_like_count: 0,
      bill_stage: '접수',
      title: '',
      bill_result: '',
    },
    representative_proposer_dto_list: [],
    public_proposer_dto_list: [],
    is_book_mark: false,
    similar_bills: [],
    vote_result_response: {
      approval_count: 0,
      total_vote_count: 0,
      party_vote_list: [],
    },
  };
}

describe('filterUniqueBills', () => {
  it('keeps the first bill when an infinite-scroll page boundary appends the same bill again', () => {
    const firstPage = [createBill('bill-1'), createBill('bill-2'), createBill('bill-3', 'first copy')];
    const secondPage = [createBill('bill-3', 'duplicate copy'), createBill('bill-4')];

    const uniqueBills = filterUniqueBills([...firstPage, ...secondPage]);

    expect(uniqueBills.map((bill) => bill.bill_info_dto.bill_id)).toEqual(['bill-1', 'bill-2', 'bill-3', 'bill-4']);
    expect(uniqueBills[2].bill_info_dto.bill_name).toBe('first copy');
  });

  it('drops bills without an id because they cannot be keyed safely in the feed', () => {
    const billWithoutId = createBill('');

    expect(filterUniqueBills([billWithoutId, createBill('bill-1')]).map((bill) => bill.bill_info_dto.bill_id)).toEqual([
      'bill-1',
    ]);
  });
});
