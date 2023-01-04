import { gql } from "@apollo/client";
import { EntityType } from "../types";

export const DEFAULT_ENTITY = gql`
  query DefaultEntity {
    defaultEntity {
      id
      type
      name
    }
  }
`;

export interface DefaultEntityResult {
  defaultEntity: {
    id: string;
    type: EntityType;
    name: string;
  };
}

export interface DefaultEntityVars {}
