import { gql } from "@apollo/client";

export const GET_CITATION_BY_GUID = gql`
  query CitationQuery($citationGUID: String!) {
    GetCitationByGUID(citationGUID: $citationGUID) {
      guid
      text
      meta {
        title
        author
        publisher
      }
    }
  }
`;

export interface GetCitationByGUIDResult {
  GetCitationByGUID: {
    guid: string;
    text: string;
    meta: {
      title: string;
      author: string;
      publisher: string;
    };
  };
}

export interface GetCitationByGUIDVars {
  citationGUID: string;
}
