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
        console.log('payload.guids is ', payload.guids)
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
