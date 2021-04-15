"use strict";
/*
Model definition for document TimeTag
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
exports.TimeTagTypes = void 0;
const mongoose_1 = __importStar(require("mongoose"));
var TimeTagTypes;
(function (TimeTagTypes) {
    TimeTagTypes["Range"] = "Year:Year";
    TimeTagTypes["Year"] = "Year";
    TimeTagTypes["Season"] = "Year:Quarter";
    TimeTagTypes["Month"] = "Year:Month";
    TimeTagTypes["Day"] = "Year:Month:Day";
})(TimeTagTypes = exports.TimeTagTypes || (exports.TimeTagTypes = {}));
const TimeTag = new mongoose_1.Schema({
    // lookup a Time:
    // what names are associated with them?
    // which timetags are associated with them?
    guid: { type: String, index: true, required: true },
    type: TimeTagTypes,
});
exports.default = mongoose_1.default.model('TimeTag', TimeTag);
//# sourceMappingURL=timeTag.js.map