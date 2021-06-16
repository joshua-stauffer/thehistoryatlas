import { gql } from "@apollo/client";

export const GET_SUMMARIES_BY_GUID = gql`
  query SummaryQuery($summary_guids: [String!]!) {
    GetSummaryByGUIDs(summary_guids: $summary_guids) {
      guid
      text
      tags {
        tag_type
        tag_guid
        start_char
        stop_char
      }
    }
  }
`;

export interface GetSummariesByGUIDResult {
  GetSummaryByGUIDs: {
    guid: string;
    text: string;
    tags: {
      tag_type: string;
      tag_guid: string;
      start_char: number;
      stop_char: number;
    }[]
  }[]
}

export interface GetSummariesByGUIDVars {
  summary_guids: string[];
}
