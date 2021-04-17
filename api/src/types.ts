/*
Collection of application-wide types
April 16th, 2021
*/

export interface BoundingBox {
  upperLeft: number;
  bottomRight: number;
}

export interface Location {
  point: Point;
  shape?: Point[];             // may need to adjust this to work with geojson better
}

export interface Point {
  latitude: number;
  longitude: number;
}

export interface PlaceSummaryByTimeTag {
  placeName: string[];
  placeLocation: Location;
  citationCount: number;
  personCount: number;
}

export interface TimeTagByFocus {
  citations: Citation[];
  adjacentPeople: Person[];
}

export interface Citation {
  text: string;
  tags: Tag[];
  meta: MetaData;
}

export interface Tag {
  type: FocusType;
  guid: string;
  start: number;
  end: number;
}

export interface MetaData {
  author: string;
  publisher: string;
  pubDate: string;
  pageNum: number;
}

export interface Person {
  guid: string;
  names: string[];
}

export type FocusType = "TIME" | "PERSON" | "PLACE";
