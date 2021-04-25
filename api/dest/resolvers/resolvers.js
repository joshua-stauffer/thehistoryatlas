"use strict";
// Resolver for the History Atlas Apollo GraphQL API
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolvers = void 0;
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
            try {
                const { payload } = await queryReadModel(msg);
                console.log('received result: ', payload);
                return payload.timeTagSummaries;
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        },
        TimeTagDetails: async (_, { focusGUID, timeTagGUID }, { queryReadModel }) => {
            const msg = {
                type: "GET_TIME_TAG_DETAILS",
                payload: {
                    focusGUID: focusGUID,
                    timeTagGUID: timeTagGUID
                }
            };
            try {
                const { payload } = await queryReadModel(msg);
                console.log('received results from timeTagDetails: ', payload);
                return payload.citations;
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        },
        SearchFocusByName: async (_, { focusType, searchTerm }, { queryReadModel }) => {
            const msg = {
                type: "SEARCH_FOCUS_BY_NAME",
                payload: {
                    focusType: focusType,
                    searchTerm: searchTerm
                }
            };
            try {
                const { payload } = await queryReadModel(msg);
                console.log('received results from searchFocusByName: ', payload);
                return payload; // double check that this is correct
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        }
    },
    Mutation: {
        AddAnnotatedCitation: async (_, { annotatedCitation }, { emitCommand }) => {
            try {
                const result = await emitCommand({
                    type: 'PUBLISH_NEW_CITATION',
                    timestamp: new Date().toJSON(),
                    // TODO: update this to reflect the current user
                    user: 'test-user',
                    payload: annotatedCitation
                });
                console.log('received result from emitting command ', result);
                return {
                    code: 'Success',
                    success: true,
                    message: 'Your command has been submitted for processing (oops not really)'
                };
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        }
    }
}; // end of Resolvers
//# sourceMappingURL=resolvers.js.map