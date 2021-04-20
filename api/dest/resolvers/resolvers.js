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
            // combines the two GUIDs to create a new value and looks up citations 
            // associated with that particular value
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
    },
};
//# sourceMappingURL=resolvers.js.map