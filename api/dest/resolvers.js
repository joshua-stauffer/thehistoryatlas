"use strict";
// Resolver for the History Atlas Apollo GraphQL API
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolvers = void 0;
const uuid_1 = require("uuid");
const APP_VERSION = '0.1.0';
exports.resolvers = {
    Query: {
        GetCitationsByGUID: async (_, { citationGUIDs }, { queryReadModel }) => {
            const msg = {
                type: "GET_CITATIONS_BY_GUID",
                payload: {
                    citation_guids: citationGUIDs,
                }
            };
            try {
                console.info(`Publishing query`, msg);
                const { payload } = await queryReadModel(msg);
                console.log('received result: ', payload);
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
        GetManifest: async (_, { entityType, GUID }, { queryReadModel }) => {
            const msg = {
                type: "GET_MANIFEST",
                payload: {
                    type: entityType,
                    guid: GUID
                }
            };
            try {
                console.info(`Publishing query `, msg);
                console.info(msg.payload);
                const { payload } = await queryReadModel(msg);
                console.log('received result: ', payload);
                return {
                    guid: payload.guid,
                    citation_guids: payload.citation_guids
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
                console.info(`Publishing query ${msg}`);
                const { payload } = await queryReadModel(msg);
                console.log('received result: ', payload);
                console.log('payload.guids is ', payload.guids);
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
        PublishNewCitation: async (_, { AnnotatedCitation }, { emitCommand }) => {
            console.log('Publishing the following command: ', AnnotatedCitation);
            const payload = {
                ...AnnotatedCitation,
                GUID: uuid_1.v4()
            };
            try {
                const result = await emitCommand({
                    type: 'PUBLISH_NEW_CITATION',
                    app_version: APP_VERSION,
                    timestamp: new Date().toJSON(),
                    // TODO: update this to reflect the current user
                    user: 'test-user',
                    payload: payload
                });
                console.log('received result from emitting command ', result);
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
                    message: err
                };
            }
        }
    }
}; // end of Resolvers
//# sourceMappingURL=resolvers.js.map