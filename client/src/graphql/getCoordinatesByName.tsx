import { gql } from "@apollo/client";

export const GET_COORDINATES_BY_NAME = gql`
  query GetCoordinatesByName($name: String!) {
    GetCoordinatesByName(name: $name) {
      longitude
      latitude
    }
  }
`

export interface CoordinatesByNameResult {
  GetCoordinatesByName: {
    latitude: number;
    longitude: number
  }[]
}

export interface CoordinatesByNameVars {
  name: string;
}
