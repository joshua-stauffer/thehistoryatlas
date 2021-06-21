// global type definitions

export type EntityType = "PERSON" | "PLACE" | "TIME";

export interface Entity {
  guid: string;
  type: EntityType;
}

export interface HistoryEntity {
  entity: Entity;
  rootEventID?: string;
}