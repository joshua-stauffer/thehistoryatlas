import { gql } from "@apollo/client";
import { Tag } from "../types";

export const GET_SUMMARIES_BY_GUID = gql`
  query SummaryQuery($summary_guids: [String!]!) {
    GetSummariesByGUID(summary_guids: $summary_guids) {
      guid
      text
      tags {
        tag_type
        tag_guid
        start_char
        stop_char
        names
        name
        coords {
          latitude
          longitude
        }
      }
      citation_guids
    }
  }
`;

export interface GetSummariesByGUIDResult {
  GetSummariesByGUID: Summary[];
}

export interface GetSummariesByGUIDVars {
  summary_guids: string[];
}

export interface Summary {
  guid: string;
  text: string;
  tags: Tag[];
  citation_guids: string[];
}
