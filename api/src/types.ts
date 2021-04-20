/*
Collection of application-wide types
April 16th, 2021
*/

export interface Message {
  type: string;
  payload: unknown;
}

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
  GUID: string;
  start: number;
  end: number;
}

export interface MetaData {
  author: string;
  publisher: string;
  pubDate?: string;
  pageNum?: number;
}

export interface Person {
  GUID: string;
  names: string[];
}

// starting over April 19th 2021
// anything above here is not necessarily used

export type FocusType = "TIME" | "PERSON" | "PLACE";


export interface FocusSummary {
  GUID: string;
  timeTagSummaries: TimeTagSummary[]
}

export interface TimeTagSummary {
  timeTag: string;
  GUID: string;
  citationCount: number;   // how many citations does this focus have in this time tag?
}

export interface TimeTagDetail {
  GUID: string;
  citations: Citation[]
}

export interface FocusSummaryArgs {
  focusType: FocusType;
  focusGUID: string;
}

export interface TimeTagDetailsArgs {
  focusGUID: string;
  timeTagGUID: string;
}

export interface ReadModelQuery {
  type: string;
  payload: {
      boundingBox?: BoundingBox;
      location?: Location;
      point?: Point;
      placeSummaryByTimeTag?: PlaceSummaryByTimeTag;
      person?: Person;
      metaData?: MetaData;
      tag?: Tag;
      timeTagByFocus?: TimeTagByFocus;
      focusType?: FocusType;
      GUID?: string; // testing purposes
    }
}

export type ReadModelResponse = FailedReadModelResponse | SuccessfulReadModelResponse;

interface FailedReadModelResponse {
  type: "ERROR";
  payload: {
    message: string;
  }
}

interface SuccessfulReadModelResponse {
  type: "QUERY_RESPONSE";
  payload: FocusSummary | TimeTagDetail;
}
