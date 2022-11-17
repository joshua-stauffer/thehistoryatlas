import { gql } from "@apollo/client";

export const GET_ENTITY_SUMMARIES_BY_GUID = gql`
  query GetEntitySummariesByGUID($guids: [String!]!) {
    GetEntitySummariesByGUID(guids: $guids) {
      first_citation_date
      last_citation_date
      names
      citation_count
      type
      guid
    }
  }
`;

export interface GetEntitySummariesByGUIDResult {
  GetEntitySummariesByGUID: {
    first_citation_date: string;
    last_citation_date: string;
    names: string[];
    citation_count: number;
    type: "PERSON" | "PLACE" | "TIME"
    guid: string;
  }[]
}


export interface GetEntitySummariesByGUIDVars {
  guids: string[];
}