import { gql } from "@apollo/client";
import { EntityType } from '../types';

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
      type: EntityType;
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