export interface PartyDetailResponse {
  party_id: number;
  party_name: string;
  party_img_url: string;
  total_congressman_count: number;
  proportional_congressman_count: number;
  district_congressman_count: number;
  representative_bill_count: number;
  public_bill_count: number;
  follow_count: number;
  website_url: string;
  followed: boolean;
}
