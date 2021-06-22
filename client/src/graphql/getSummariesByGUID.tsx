import { gql } from "@apollo/client";

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
    }
  }
`;

export interface GetSummariesByGUIDResult {
  GetSummariesByGUID: {
    guid: string;
    text: string;
    tags: {
      tag_type: string;
      tag_guid: string;
      start_char: number;
      stop_char: number;
      name?: string;
      names?: string[];
      coords?: {
        latitude: number;
        longitude: number;
      }
    }[]
  }[]
}

export interface GetSummariesByGUIDVars {
  summary_guids: string[];
}
