"use strict";
// Resolver for the History Atlas Apollo GraphQL API
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolvers = void 0;
const APP_VERSION = '0.1.0';
exports.resolvers = {
    Query: {
        GetSummariesByGUID: async (_, { summary_guids }, { queryReadModel }) => {
            const msg = {
                type: "GET_SUMMARIES_BY_GUID",
                payload: {
                    summary_guids: summary_guids
                }
            };
            try {
                console.debug(`Publishing query`, msg);
                const { payload } = await queryReadModel(msg);
                console.debug('received result: ', payload);
                return payload.summaries;
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        },
        GetCitationByGUID: async (_, { citationGUID }, { queryReadModel }) => {
            const msg = {
                type: "GET_CITATION_BY_GUID",
                payload: {
                    citation_guid: citationGUID
                }
            };
            try {
                console.debug(`Publishing query`, msg);
                const { payload } = await queryReadModel(msg);
                console.debug('received result: ', payload);
                return payload.citation;
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        },
        GetManifest: async (_, { entityType, GUID }, { queryReadModel }) => {
            const msg = {
                type: "GET_MANIFEST",
                payload: {
                    type: entityType,
                    guid: GUID
                }
            };
            try {
                console.debug(`Publishing query `, msg);
                console.debug(msg.payload);
                const { payload } = await queryReadModel(msg);
                console.debug('received result: ', payload);
                return {
                    guid: payload.guid,
                    citation_guids: payload.citation_guids,
                    timeline: payload.timeline
                };
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        },
        GetGUIDsByName: async (_, { name }, { queryReadModel }) => {
            const msg = {
                type: "GET_GUIDS_BY_NAME",
                payload: {
                    name: name,
                }
            };
            try {
                console.debug(`Publishing query ${msg}`);
                const { payload } = await queryReadModel(msg);
                console.debug('received result: ', payload);
                console.debug('payload.guids is ', payload.guids);
                return payload;
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        },
        GetCoordinatesByName: async (_, { name }, { queryGeo }) => {
            const msg = {
                type: "GET_COORDS_BY_NAME",
                payload: {
                    "name": name
                }
            };
            try {
                console.debug(`Publishing query `, msg);
                console.debug(msg.payload);
                const { payload } = await queryGeo(msg);
                console.debug('received result: ', payload);
                const geoResult = payload.coords[name];
                if (!geoResult)
                    throw new Error(`GeoService returned unknown result: ${geoResult}`);
                return geoResult;
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err
                };
            }
        },
        GetTextAnalysis: async (_, { text }, { queryNLP }) => {
            const msg = {
                type: "PROCESS_TEXT",
                payload: {
                    "text": text
                }
            };
            try {
                console.debug(`Publishing query `, msg);
                console.debug(msg.payload);
                const { payload } = await queryNLP(msg);
                console.debug('received result: ', payload);
                return payload;
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
        PublishNewCitation: async (_, { Annotation }, { emitCommand }) => {
            console.debug('Publishing the following command: ', Annotation);
            const payload = Annotation;
            try {
                const result = await emitCommand({
                    type: 'PUBLISH_NEW_CITATION',
                    app_version: APP_VERSION,
                    timestamp: new Date().toJSON(),
                    // TODO: update this to reflect the current user
                    user: 'test-user',
                    payload: payload
                });
                console.debug('received result from emitting command ', result);
                if (result.type === 'COMMAND_FAILED') {
                    let message;
                    if (result.payload) {
                        message = 'Your Citation has not been processed due to an error: ' + result.payload.reason;
                    }
                    else {
                        message = 'Your Citation has not been processed due to an error.';
                    }
                    return {
                        code: 'Failure',
                        success: false,
                        message: message
                    };
                }
                return {
                    code: 'Success',
                    success: true,
                    message: 'Your Citation has been processed'
                };
            }
            catch (err) {
                return {
                    code: 'Error',
                    success: false,
                    message: err // this may run the risk of exposing sensitive data -- debug only
                };
            }
        }
    }
}; // end of Resolvers
//# sourceMappingURL=resolvers.js.map