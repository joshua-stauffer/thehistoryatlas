/*

*/
import { Context } from '../index';
import {
  FocusSummary,
  FocusSummaryArgs,
  Message,
  ReadModelResponse
} from '../types'


type ResolverFn = (parent: any, args: any, ctx: any) => any;
interface ResolverMap {
  [field: string]: ResolverFn;
}
interface Resolvers {
  Query: ResolverMap;
}


// import { timeTagDetails, personSummaryData } from './fakeData';

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
        const { payload } = await queryReadModel(msg) as ReadModelResponse;
        console.log('received result: ', payload)
        return payload.timeTagSummaries as FocusSummary

      // local data for testing
      // return personSummaryData.find(s => s.GUID === focusGUID)?.timeTagSummaries
    },

    TimeTagDetails: async (_, 
      { focusGUID, timeTagGUID },
      { queryReadModel }: Context) => {
        // combines the two GUIDs to create a new value and looks up citations 
        // associated with that particular value

      const msg = {
        type: "GET_TIME_TAG_DETAILS",
        payload: {
          focusGUID: focusGUID,
          timeTagGUID: timeTagGUID
        }
      }
      const { payload } = await queryReadModel(msg);
      console.log('received results from timeTagDetails: ', payload)
      return payload.citations
      // local data for testing
      // return timeTagDetails.find(tt => tt.GUID === combinedGUID)?.citations
    },

  },


}
