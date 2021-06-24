// Resolver for the History Atlas Apollo GraphQL API

import { Context } from './index';
import { Resolver, WriteModelResponse } from './types'

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

    GetSummariesByGUID: async (_,
      { summary_guids }: Resolver.GetSummariesByGUIDsArgs,
      { queryReadModel }: Context) => {
      const msg = {
        type: "GET_SUMMARIES_BY_GUID",
        payload: {
          summary_guids: summary_guids
        }
      }
      try {
        console.debug(`Publishing query`, msg)
        const { payload } = await queryReadModel(msg) as Resolver.SummariesByGUID;
        console.debug('received result: ', payload)
        return payload.summaries
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },
    
    GetCitationByGUID: async (_,
      { citationGUID }: Resolver.GetCitationByGUIDsArgs,
      { queryReadModel }: Context) => {
        const msg = {
          type: "GET_CITATION_BY_GUID",
          payload: {
            citation_guid: citationGUID
          }
        }
        try {
          console.debug(`Publishing query`, msg)
          const { payload } = await queryReadModel(msg) as Resolver.CitationByGUID;
          console.debug('received result: ', payload)
          return payload.citation
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
        console.debug(`Publishing query `, msg)
        console.debug(msg.payload)

        const { payload } = await queryReadModel(msg) as Resolver.Manifest;
        console.debug('received result: ', payload)
        return {
          guid: payload.guid,
          citation_guids: payload.citation_guids,
          timeline: payload.timeline
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
        console.debug(`Publishing query ${msg}`)
        const { payload } = await queryReadModel(msg) as Resolver.GUIDByName;
        console.debug('received result: ', payload)
        console.debug('payload.guids is ', payload.guids)
        return payload
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },
    GetCoordinatesByName: async (_,
      { name }: Resolver.GetCoordinatesByNameArgs,
      { queryGeo }: Context) => {
      const msg = {
        type: "GET_COORDS_BY_NAME",
        payload: {
          "name": name
        }
      }
      try {
        console.debug(`Publishing query `, msg)
        console.debug(msg.payload)

        const { payload } = await queryGeo(msg) as Resolver.CoordsByName;
        console.debug('received result: ', payload);
        const geoResult = payload.coords[name];
        if (!geoResult) throw new Error(`GeoService returned unknown result: ${geoResult}`);
        return geoResult
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },
    GetTextAnalysis: async (_,
      { text }: Resolver.GetTextAnalysisArgs,
      { queryNLP }: Context) => {
      const msg = {
        type: "PROCESS_TEXT",
        payload: {
          "text": text
        }
      }
      try {
        console.debug(`Publishing query `, msg)
        console.debug(msg.payload)

        const { payload } = await queryNLP(msg) as Resolver.TextProcessed;
        console.debug('received result: ', payload);
        return payload
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
      { Annotation }: Resolver.PublishNewCitationArgs,
      { emitCommand }: Context) => {
        console.debug('Publishing the following command: ', Annotation)
        const payload = Annotation;
        try {
          const result = await emitCommand({
            type: 'PUBLISH_NEW_CITATION',
            app_version: APP_VERSION,
            timestamp: new Date().toJSON(),
            // TODO: update this to reflect the current user
            user: 'test-user',
            payload: payload
          }) as WriteModelResponse;
          console.debug('received result from emitting command ', result)
          if (result.type === 'COMMAND_FAILED') {
            let message: string;
            if (result.payload) {
              message = 'Your Citation has not been processed due to an error: ' + result.payload.reason
            } else {
              message = 'Your Citation has not been processed due to an error.'
            }
            return {
              code: 'Failure',
              success: false,
              message: message
            }
          }
          return {
            code: 'Success',
            success: true,
            message: 'Your Citation has been processed'
          }
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err // this may run the risk of exposing sensitive data -- debug only
          }
        }
      }
  }
} // end of Resolvers
