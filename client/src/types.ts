// global type definitions

export type EntityType = "PERSON" | "PLACE" | "TIME";

export interface Entity {
  guid: string;
  type: EntityType;
  name: string;
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

export interface CurrentFocus {
  focusedGUID: string;
  scrollIntoView: boolean;
}

export type Tag = PlaceTag | TimeTag | PersonTag;

export interface PlaceTag {
  tag_type: "PLACE";
  tag_guid: string;
  start_char: number;
  stop_char: number;
  names: string[];
  coords: {
    latitude: number;
    longitude: number;
  }
}

export interface TimeTag {
  tag_type: "TIME";
  tag_guid: string;
  start_char: number;
  stop_char: number;
  name: string;
}

export interface PersonTag {
  tag_type: "PERSON";
  tag_guid: string;
  start_char: number;
  stop_char: number;
  names: string[];
}
