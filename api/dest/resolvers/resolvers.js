"use strict";
/*

*/
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolvers = void 0;
exports.resolvers = {
    Query: {
        placeSummary() {
            return [placeSummary];
        },
    }
};
const placeSummary = {
    placeName: ['Rome', 'Roma'],
    placeLocation: {
        point: {
            latitude: 100,
            longitude: 100
        }
    },
    citationCount: 35,
    personCount: 12
};
//# sourceMappingURL=resolvers.js.map