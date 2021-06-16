import { gql } from "@apollo/client";

export const GET_MANIFEST = gql`
  query ManifestQuery($entityType: EntityType!, $GUID: String!) {
    GetManifest(entityType: $entityType, GUID: $GUID) {
      guid
      citation_guids
    }
  }
`;


export interface GetManifestResult {
  GetManifest: {
    guid: string;
    citation_guids: string[];
  }
}

export interface GetManifestVars {
  GUID: string;
  entityType: String;
}
