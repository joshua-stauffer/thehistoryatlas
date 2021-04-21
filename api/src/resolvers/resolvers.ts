// Resolver for the History Atlas Apollo GraphQL API

import { Context } from '../index';
import {
  FocusSummary,
  FocusSummaryArgs,
  ReadModelResponse,
  Schema
} from '../types'


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
  }, // end of Query

  Mutation: {

    AddAnnotatedCitation: async (_,
      { annotatedCitation }: Schema.AnnotatedCitationArgs,
      { emitCommand }: Context) => {
        try {
          const result = await emitCommand({
            type: 'PUBLISH_NEW_CITATION',
            payload: annotatedCitation
          })
          console.log('received result from emitting command ', result)
          return {
            code: 'Success',
            success: true,
            message: 'Your command has been submitted for processing (oops not really)'
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
