/*

*/
import { Context } from '../index';
import {
  FocusSummary,
  FocusSummaryArgs,
  TimeTagDetailsArgs,
  Message
} from '../types'


type ResolverFn = (parent: any, args: any, ctx: any) => any;
interface ResolverMap {
  [field: string]: ResolverFn;
}
interface Resolvers {
  Query: ResolverMap;
}


import { timeTagDetails, personSummaryData } from './fakeData';

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
        const result = await queryReadModel(msg) as Message;
        console.log('received result: ', result)
        return result.payload.timeTagSummaries as FocusSummary

      // fake local data:
      // return personSummaryData.find(s => s.GUID === focusGUID)?.timeTagSummaries
    },

    TimeTagDetails: (_, { focusGUID, timeTagGUID }, ___) => {
      const combinedGUID = timeTagGUID + focusGUID
      return timeTagDetails.find(tt => tt.GUID === combinedGUID)?.citations
    },

  },


}
