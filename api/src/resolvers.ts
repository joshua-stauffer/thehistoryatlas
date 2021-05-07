// Resolver for the History Atlas Apollo GraphQL API

import { v4 } from 'uuid';
import { Context } from './index';
import {
  GetCitationsByGUIDsArgs,
  Resolver
} from './types'

const APP_VERSION = '0.1.0'

type ResolverFn = (parent: any, args: any, ctx: any) => any;
interface ResolverMap {
  [field: string]: ResolverFn;
}
interface Resolvers {
  Query: ResolverMap;
  Mutation: ResolverMap;
}

export const resolvers: Resolvers = {
  Query: {
    GetCitationsByGUID: async (_,
      { citationGUIDs }: GetCitationsByGUIDsArgs,
      { queryReadModel }: Context) => {
        const msg = {
          type: "GET_CITATIONS_BY_GUID",
          payload: {
            citation_guids: citationGUIDs,
          }
        }
        try {
          console.info(`Publishing query`, msg)
          const { payload } = await queryReadModel(msg) as Resolver.CitationsByGUID;
          console.log('received result: ', payload)
          return payload.citations
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
    },
    GetManifest: async (_,
      { entityType, GUID }: Resolver.GetManifestArgs,
      { queryReadModel }: Context) => {
      const msg = {
        type: "GET_MANIFEST",
        payload: {
          type: entityType,
          guid: GUID
        }
      }
      try {
        console.info(`Publishing query `, msg)
        console.info(msg.payload)

        const { payload } = await queryReadModel(msg) as Resolver.Manifest;
        console.log('received result: ', payload)
        return {
          guid: payload.guid,
          citation_guids: payload.citation_guids
        }
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },
    GetGUIDsByName: async (_,
      { name }: Resolver.GetGUIDsByNameArgs,
      { queryReadModel }: Context) => {
      const msg = {
        type: "GET_GUIDS_BY_NAME",
        payload: {
          name: name,
        }
      }
      try {
        console.info(`Publishing query ${msg}`)
        const { payload } = await queryReadModel(msg) as Resolver.GUIDByName;
        console.log('received result: ', payload)
        return payload.guids
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    }
    

  }, // end of Query

  Mutation: {

    PublishNewCitation: async (_,
      { AnnotatedCitation }: Resolver.PublishNewCitationArgs,
      { emitCommand }: Context) => {
        console.log('Publishing the following command: ', AnnotatedCitation)
        const payload = {
          ...AnnotatedCitation,
          GUID: v4()
        }
        try {
          const result = await emitCommand({
            type: 'PUBLISH_NEW_CITATION',
            app_version: APP_VERSION,
            timestamp: new Date().toJSON(),
            // TODO: update this to reflect the current user
            user: 'test-user',
            payload: payload
          })
          console.log('received result from emitting command ', result)
          return {
            code: 'Success',
            success: true,
            message: 'Your Citation has been processed'
          }
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      }
  }
} // end of Resolvers


/*

    FocusSummary: async (_,
      { focusGUID, focusType }: FocusSummaryArgs,
      { queryReadModel }: Context) => {

        const msg = {
          type: "GET_FOCUS_SUMMARY",
          payload: {
            focusType: focusType,
            GUID: focusGUID
          }
        }
        try {
          const { payload } = await queryReadModel(msg) as ReadModelResponse;
          console.log('received result: ', payload)
          return payload.timeTagSummaries as FocusSummary  
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
    },

    TimeTagDetails: async (_, 
      { focusGUID, timeTagGUID },
      { queryReadModel }: Context) => {
      const msg = {
        type: "GET_TIME_TAG_DETAILS",
        payload: {
          focusGUID: focusGUID,
          timeTagGUID: timeTagGUID
        }
      }
      try {
        const { payload } = await queryReadModel(msg);
        console.log('received results from timeTagDetails: ', payload)
        return payload.citations
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },

    SearchFocusByName: async (_,
      { focusType, searchTerm },
      { queryReadModel }: Context) => {
        const msg = {
          type: "SEARCH_FOCUS_BY_NAME",
          payload: {
            focusType: focusType,
            searchTerm: searchTerm
          }
        }
        try {
          const { payload } = await queryReadModel(msg);
          console.log('received results from searchFocusByName: ', payload)
          return payload // double check that this is correct
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      }
*/