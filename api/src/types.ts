/*
Collection of application-wide types
April 16th, 2021
*/



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

export interface Location {
  latitude: number;
  longitude: number;
  geoshape: string;
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

export interface WriteModelResponse {
  type: string;
  payload?: {
    reason: string;
    existing_event_guid?: string;
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
  payload: CitationsByGUID;
}

export interface ReadModelQuery {
  type: string;
  payload: {
    citation_guid?: string;
    summary_guids?: string[];
    entityType?: EntityType;
    GUID?: string;
    name?: string;
    type?: EntityType;
    guid?: string;
  }
}

export interface NLPServiceQuery {
  type: string;
  payload: {
    text: string;
  }
}

export interface GeoServiceQuery {
  type: string;
  payload: {
    name: string;
  }
}

// type defs for GraphQL resolvers
export namespace Resolver {

  export interface GetCitationByGUIDsArgs {
    citationGUID: string;
  }
  
  export interface GetSummariesByGUIDsArgs {
    summary_guids: string[];
  }

  export interface GetManifestArgs {
    entityType: EntityType;
    GUID: string;
  }

  export interface PublishNewCitationArgs {
    Annotation: {
      citation: string;
      meta: MetaData;
      citation_guid: string;
      summary_guid: string;
      summary: string;
      summary_tags: Tag[];
    }
  }

  export interface GetGUIDsByNameArgs {
    name: string;
  }

  export interface GetCoordinatesByNameArgs {
    name: string;
  }

  export interface GetTextAnalysisArgs {
    text: string;
  }
  // Query results



  export interface SummariesByGUID {
    type: string;
    payload: {
      summaries: Summary[];
    }
  }

  export interface Summary {
    guid: string;
    text: string;
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
    }
  }

  export interface CitationByGUID {
    type: string;
    payload: {
      citation: {
        citation_guid: {
          text: string;
          meta: {
            title: string;
            author: string;
            publisher: string;
            pubDate?: string;
            pageNum?: number;
          }
        }
      }
    }
  }

  export interface Manifest {
    type: string;
    payload: {
      guid: string;
      citation_guids: string[];
      timeline: {
        year: number;
        count: number;
        base_guid: string;
      }[]
    }
  }

  export interface GUIDByName {
    type: string;
    payload: {
      guids: string[]
    }
  }

  export interface CoordsByName {
    type: string;
    payload: {
      coords: {
        [key: string]: Location;
      }
    }
  }

  export interface TextProcessed {
    type: string;
    payload: {
      text: string;
      text_map: {
        [key: string]: {
          text: string;
          start_char: number;
          stop_char: number;
          guids: string[];
          coords?: Location[]
        }
      }
    }
  }

}

export namespace Schema {
  // migrate to using this namespace for any type defined inside the GraphQL Schema

  
}