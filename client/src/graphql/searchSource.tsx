import { gql } from "@apollo/client";

export const SEARCH_SOURCES = gql`
  query SearchSources($searchTerm: String!) {
    searchSources(searchTerm: $searchTerm) {
      id
      title
      author
      publisher
      pubDate
    }
  }
`;

export interface SearchSourcesResult {
  searchSources: {
    id: string;
    title: string;
    author: string;
    publisher: string;
    pubDate: string;
  }[];
}

export interface SearchSourcesVars {
  searchTerm: string;
}
