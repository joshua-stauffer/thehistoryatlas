// Globally useful type definitions
// Namespaces
//  APITypes: all types that need to stay in sync with the API service
//  DB: types related to getting data in and out of the database

// Global types
type FocusType = "PERSON" | "PLACE" | "TIME";

export namespace APITypes {
  // all types related to the API component
  
  export interface QueryResponse {
    type: string;
    payload: unknown;
  }

  export interface ErrorResponse extends QueryResponse {
    type: "ERROR";
    result: {
      message: string;
    }
  }

  // FOCUS_SUMMARY
  export interface FocusSummaryQuery {
    focusType: FocusType;
    GUID: string;
  }
  export interface FocusSummaryResponse extends QueryResponse {
    type: string;
    payload: {
      GUID: string;
      timeTagSummaries: DB.TimeTagSummary[]
    }
  }

  // TIME_TAG_DETAILS
  export interface TimeTagDetailsQuery {
    focusGUID: string;
    timeTagGUID: string;
  }

  export interface TimeTagDetailsResponse extends QueryResponse {
    type: string;
    payload: {
      citations: DB.Citation[]
    }
  }

  // NAME_TAG
  export interface NameTagQuery {
    name: string;
  }
}

export namespace DB {

  // TimeTagByFocus definitions
  export interface Citation {
    GUID: string;
    tags: Tag[]
    text: string;
    meta: CitationMetadata;
  }
  
  export interface CitationMetadata {
    author: string;
    publisher: string;
    pubDate?: string;
    pageNum?: number;
  }

  export interface Tag {
    type: FocusType;
    GUID: string;
    start: number;
    end: number;
  }

  // FocusSummary definitions
  export interface TimeTagSummary {
    timeTag: string;
    GUID: string;
    citationCount: number;
  }
  
}