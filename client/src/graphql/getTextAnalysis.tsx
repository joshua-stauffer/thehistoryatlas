import { gql } from "@apollo/client";

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