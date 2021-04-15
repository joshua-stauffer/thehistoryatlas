"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const mongoose_1 = require("mongoose");
const PersonTag = new mongoose_1.Schema({
    // lookup a person by guid
    guid: { type: String, index: true, required: true },
    names: [{ type: String }],
    orderedTimeTags: [{ type: String }] // a list of time tag GUIDS representing chronological events
});
//# sourceMappingURL=personTag.js.map