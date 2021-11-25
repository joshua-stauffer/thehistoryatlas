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

export type AccountsServiceQuery = Accounts.Query


export namespace Accounts {


  export interface Message {
    type: QueryType;
    payload: PayloadType;
  }

  export type Query =
    AddUserQuery
    | GetUserQuery
    | UpdateUserQuery
    | IsUsernameUniqueQuery
    | DeactivateAccountQuery
    | ConfirmAccountQuery
    | LoginQuery

  export type QueryType = 
    'LOGIN' 
    | 'ADD_USER'
    | 'GET_USER'
    | 'UPDATE_USER'
    | 'IS_USERNAME_UNIQUE'
    | 'DEACTIVATE_ACCOUNT'
    | 'CONFIRM_ACCOUNT';

  export type PayloadType =
    LoginPayload
    | AddUserPayload
    | GetUserPayload
    | IsUsernameUniquePayload
    | DeactivateAccountPayload
    | ConfirmAccountPayload

  export interface UserDetails {
    f_name: string;
    l_name: string;
    email: string;
    password: string;
  }

  export interface AccountResult {
    // standard AccountService result object
    token: string;
    user_details: UserDetails;
  }

  export interface LoginPayload {
    username: string;
    password: string;
  }

  export interface LoginQuery {
    type: 'LOGIN';
    payload: LoginPayload
  }

  export interface LoginResult {
    type: 'LOGIN';
    payload: {
      success: boolean;
      token?: string;
    }
  }

  export interface AddUserQuery {
    type: 'ADD_USER',
    payload: {
      token: string;
      user_details: UserDetails
    }
  }

  export interface AddUserPayload {
    token: string;
    user_details: UserDetails
  }

  export interface AddUserResult {
    type: 'ADD_USER'
    payload: AccountResult
  }

  export interface UpdateUserQuery {
    type: 'UPDATE_USER',
    payload: UpdateUserPayload
  }

  export interface UpdateUserPayload {
    token: string;
    user_details: UserDetails;
  }

  export interface UpdateUserResponse {
    type: 'UPDATE_USER';
    payload: UpdateUserPayload;
  }

  export interface GetUserQuery {
    type: 'GET_USER';
    payload: GetUserPayload
  }

  export interface GetUserPayload {
    token: string;
  }

  export interface GetUserResult {
    type: 'GET_USER'
    payload: {
      token: string;
      user_details: UserDetails
    }
  }

  export interface IsUsernameUniqueQuery {
    type: 'IS_USERNAME_UNIQUE',
    payload: IsUsernameUniquePayload
  }

  export interface IsUsernameUniquePayload {
    username: string;
  }

  export interface IsUsernameUniqueResult {
    type: "IS_USERNAME_UNIQUE",
    payload: {
      is_unique: boolean;
      username: string;
    }
  }

  export interface DeactivateAccountQuery {
    type: 'DEACTIVATE_ACCOUNT',
    payload: DeactivateAccountPayload
  }

  export interface DeactivateAccountPayload {
    token: string;
    username: string;
  }

  export interface DeactivateAccountResult {
    type: "DEACTIVATE_ACCOUNT",
    payload: {
      token: string;
      user_details: UserDetails
    }
  }

  export interface ConfirmAccountQuery {
    type: 'CONFIRM_ACCOUNT',
    payload: ConfirmAccountPayload
  }

  export interface ConfirmAccountPayload {
    token: string;
  }

  export interface ConfirmAccountResult {
    type: "CONFIRM_ACCOUNT",
    payload: {
      token: string;
      user_details: UserDetails
    }
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