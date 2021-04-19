"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolvers = void 0;
const fakeData_1 = require("./fakeData");
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
            const result = await queryReadModel(msg);
            console.log('received result: ', result);
            return result.payload.timeTagSummaries;
            // fake local data:
            // return personSummaryData.find(s => s.GUID === focusGUID)?.timeTagSummaries
        },
        TimeTagDetails: (_, { focusGUID, timeTagGUID }, ___) => {
            const combinedGUID = timeTagGUID + focusGUID;
            return fakeData_1.timeTagDetails.find(tt => tt.GUID === combinedGUID)?.citations;
        },
    },
};
//# sourceMappingURL=resolvers.js.map