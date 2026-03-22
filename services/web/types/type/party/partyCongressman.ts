export interface PartyCongressmanProps {
  congressman_id: string;
  congressman_name: string;
  congressman_image_url: string;
}

export interface PartyCongressmanResponse {
  party_congressman: PartyCongressmanProps[];
}
