export interface SearchCongressmanPartyProps {
  party_id: number;
  party_name: string;
  party_image_url: string;
  search_type: string;
  congressman_id: string;
  congressman_image_url: string;
  congressman_name: string;
}
export interface SearchCongressmanPartyResponse {
  search_response: SearchCongressmanPartyProps[];
}
