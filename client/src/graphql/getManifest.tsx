import { gql } from "@apollo/client";

export const GET_MANIFEST = gql`
  query ManifestQuery($entityType: EntityType!, $GUID: String!) {
    GetManifest(entityType: $entityType, GUID: $GUID) {
      guid
      citation_guids
      timeline {
        year
        root_guid
        count
      }
    }
  }
`;

export interface GetManifestResult {
  GetManifest: {
    guid: string;
    citation_guids: string[];
    timeline: {
      year: number;
      root_guid: string;
      count: number;
    }[];
  };
}

export interface GetManifestVars {
  GUID: string;
  entityType: String;
}
