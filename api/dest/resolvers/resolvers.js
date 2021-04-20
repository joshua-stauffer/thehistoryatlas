"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolvers = void 0;
// import { timeTagDetails, personSummaryData } from './fakeData';
exports.resolvers = {
    Query: {
        FocusSummary: async (_, { focusGUID, focusType }, { queryReadModel }) => {
            const msg = {
                type: "GET_FOCUS_SUMMARY",
                payload: {
                    focusType: focusType,
                    GUID: focusGUID
                }
            };
            const { payload } = await queryReadModel(msg);
            console.log('received result: ', payload);
            return payload.timeTagSummaries;
            // local data for testing
            // return personSummaryData.find(s => s.GUID === focusGUID)?.timeTagSummaries
        },
        TimeTagDetails: async (_, { focusGUID, timeTagGUID }, { queryReadModel }) => {
            const msg = {
                type: "GET_TIME_TAG_DETAILS",
                payload: {
                    focusGUID: focusGUID,
                    timeTagGUID: timeTagGUID
                }
            };
            const { payload } = await queryReadModel(msg);
            console.log('received results from timeTagDetails: ', payload);
            return payload.citations;
            // local data for testing
            // return timeTagDetails.find(tt => tt.GUID === combinedGUID)?.citations
        },
        SearchFocusByName: async (_, { focusType, searchTerm }, { queryReadModel }) => {
            const msg = {
                type: "SEARCH_FOCUS_BY_NAME",
                payload: {
                    focusType: focusType,
                    searchTerm: searchTerm
                }
            };
            const { payload } = await queryReadModel(msg);
            console.log('received results from searchFocusByName: ', payload);
            return payload; // double check that this is correct
        }
    },
    Mutation: {
        AddAnnotatedCitation: async (_, { annotatedCitation }, { publishToWriteModel }) => {
            publishToWriteModel({
                type: 'PUBLISH_NEW_CITATION',
                payload: annotatedCitation
            });
            return {
                code: '200',
                success: true,
                message: 'Your command has been submitted for processing (oops not really)'
            };
        }
    }
}; // end of Resolvers
//# sourceMappingURL=resolvers.js.map