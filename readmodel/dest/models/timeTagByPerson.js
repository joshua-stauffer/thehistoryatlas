"use strict";
/*
Model definition for documents TimeTagByPerson.

Stores citations with a combined key of time tag guid + person tag guid
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
// NOTE: citation is the same here and in timeTagByCity. If you update one,
//          update the other too.
const mongoose_1 = __importStar(require("mongoose"));
const TimeTagByPerson = new mongoose_1.Schema({
    key: { type: String, index: true, required: true, unique: true },
    citations: {
        guid: String,
        placeTags: [String],
        personTags: [String],
        text: String,
        meta: {
            author: String,
            publisher: String,
            pubDate: String,
            pageNum: Number
        }
    }
});
exports.default = mongoose_1.default.model('TimeTagByPerson', TimeTagByPerson);
//# sourceMappingURL=timeTagByPerson.js.map