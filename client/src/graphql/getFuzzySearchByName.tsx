import { gql } from "@apollo/client";

export const GET_FUZZY_SEARCH_BY_NAME = gql`
  query GetFuzzySearchByName($name: String!) {
    GetFuzzySearchByName(name: $name) {
      guids
      name
    }
  }
`;

export interface GetFuzzySearchByNameResult {
  GetFuzzySearchByName: {
    name: string
    guids: string[]
  }[]
}

export interface GetFuzzySearchByNameVars {
  name: string;
}
