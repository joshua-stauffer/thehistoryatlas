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

export interface MarkerData {
  coords: [number, number],
  text: string;
  guid: string;
}

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface FocusedGeoEntity {
  GUID: string;
  coords: Coordinates;
}