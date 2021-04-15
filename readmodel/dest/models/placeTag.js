"use strict";
/*
Model definition for document PlaceTag
*/
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CoordType = void 0;
const mongoose_1 = __importStar(require("mongoose"));
var CoordType;
(function (CoordType) {
    CoordType["POINT"] = "Point";
    CoordType["REGION"] = "Region";
})(CoordType = exports.CoordType || (exports.CoordType = {}));
const Point = new mongoose_1.Schema({
    latitude: Number,
    longitude: Number
});
const Location = new mongoose_1.Schema({
    type: CoordType,
    point: Point,
    shape: [Point]
});
const PlaceTag = new mongoose_1.Schema({
    // get a city's names and location
    guid: { type: String, index: true, required: true },
    names: [{ type: String }],
    location: Location
});
exports.default = mongoose_1.default.model('PlaceTag', PlaceTag);
//# sourceMappingURL=placeTag.js.map