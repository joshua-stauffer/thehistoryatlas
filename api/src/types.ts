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
  type: EntityType;
  GUID: string;
  start_char: number;
  stop_char: number;
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

export type EntityType = "TIME" | "PERSON" | "PLACE";





export interface GetCitationsByGUIDsArgs {
  citationGUIDs: string[]
}

export interface CitationsByGUID {
  type: string;
  payload: {
    citations: {
      citation_guid: {
        text: string;
        meta: {
          title: string;
          author: string;
          publisher: string;
          pubDate?: string;
          pageNum?: number;
        }
        tags: {
          start_char: number;
          stop_char: number;
          tag_type: EntityType;
          tag_guid: string;
          name?: string;
          names?: string[];
          coords?: {
            latitude: number;
            longitude: number;
            geoshape?: string;
          }
        }[]
      }
    }
  }
}




export interface WriteModelCommand {
  type: string;
  payload: any;
  timestamp?: string;
  user?: string;
  app_version: string;
  citation_guid?: string;
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
  payload: CitationsByGUID;
}

export interface ReadModelQuery {
  type: string;
  payload: {
    citation_guids?: string[];
    entityType?: EntityType;
    GUID?: string;
    name?: string;
    type?: EntityType;
    guid?: string;
  }
}

export namespace Resolver {

  export interface GetManifestArgs {
    entityType: EntityType;
    GUID: string;
  }

  export interface PublishNewCitationArgs {
    AnnotatedCitation: {
      text: string;
      tags: Tag[];
      meta: MetaData;
    }
  }

  export interface GetGUIDsByNameArgs {
    name: string;
  }

  // Query results

  export interface CitationsByGUID {
    type: string;
    payload: {
      citations: {
        citation_guid: {
          text: string;
          meta: {
            title: string;
            author: string;
            publisher: string;
            pubDate?: string;
            pageNum?: number;
          }
          tags: {
            start_char: number;
            stop_char: number;
            tag_type: EntityType;
            tag_guid: string;
            name?: string;
            names?: string[];
            coords?: {
              latitude: number;
              longitude: number;
              geoshape?: string;
            }
          }[]
        }
      }
    }
  }

  export interface Manifest {
    type: string;
    payload: {
      guid: string;
      citation_guids: string[];
    }
  }

  export interface GUIDByName {
    type: string;
    payload: {
      guids: string[]
    }
  }

}

export namespace Schema {
  // migrate to using this namespace for any type defined inside the GraphQL Schema

  
}