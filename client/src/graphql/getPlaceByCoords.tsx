import { gql } from "@apollo/client";

export const GET_PLACE_BY_COORDS = gql`
  query GetPlaceByCoords($latitude: Float!, $longitude: Float!) {
    GetPlaceByCoords(latitude: $latitude, longitude: $longitude) {
      guid
      latitude
      longitude
    }
  }
`;

export interface GetPlaceByCoordsResult {
  GetPlaceByCoords: {
    guid: string | null;
    latitude: number;
    longitude: number;
  };
}

export interface GetPlaceByCoordsVars {
  latitude: number;
  longitude: number;
}
