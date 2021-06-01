import { gql } from "@apollo/client";

export const GET_GUIDS_BY_NAME = gql`
  query GUIDQuery($name: String!) {
    GetGUIDsByName(name: $name) {
      guids
      summaries {
        type
        guid
        citation_count
        names
        first_citation_date
        last_citation_date
      }
    }
  }
`;

export interface GUIDsByNameResult {
  GetGUIDsByName: {
    guids: string[];
    summaries: {
      type: string;
      guid: string;
      citation_count: number;
      names: string[];
      first_citation_date: string;
      last_citation_date: string;
    }[]
  }
}

export interface GUIDsByNameVars {
  name: string;
}

export const GET_TEXT_ANALYSIS = gql`
  query TextAnalysis($text: String!) {
    GetTextAnalysis(text: $text) {
      text
      text_map {
        PERSON {
          text
          start_char
          stop_char
          guids
        }
        PLACE {
          text
          start_char
          stop_char
          guids
          coords {
            latitude
            longitude
          }
        }
        TIME {
          text
          start_char
          stop_char
          guids
        }
      }
    }
  }
`;

/*

*/