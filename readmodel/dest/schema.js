"use strict";
/*
Mongoose database schema definitions for the History Atlas read sides
April 12, 2021

what am i storing here?
cityName:           coordinates
personName:         personId[]
timeTag:            guid
timeTag + person:   full citations
timeTag + city:     stubs

typical query:
choose person to focus => guid
*/
Object.defineProperty(exports, "__esModule", { value: true });
exports.TimeTagByCity = exports.TimeTagByPerson = exports.TimeTag = void 0;
const mongoose_1 = require("mongoose");
exports.TimeTag = new mongoose_1.Schema({
    // lookup a timetag -- does it exist yet?
    val: { type: String, index: true },
    GUID: { type: String, required: true, unique: true }
});
// Time Tags by Person
const CitationMeta = new mongoose_1.Schema({
    // holds citation metadata
    author: [{ type: String }],
    publisher: { type: String },
    pubDate: { type: Date },
    pageNumber: { type: Number }
});
const Citation = new mongoose_1.Schema({
    // subdoc for holding a single citation
    contributor: { type: String },
    text: { type: String },
    meta: CitationMeta,
    // tags
    personTags: [{ type: String }] // guids
});
exports.TimeTagByPerson = new mongoose_1.Schema({
    // primary holder for citations
    // keys are TimeTag string + personGUID
    key: { type: String, required: true, unique: true, index: true },
    citations: [Citation]
});
// Time Tags by City 
const CitationStub = new mongoose_1.Schema({
    personGUIDS: [{ type: String }]
});
exports.TimeTagByCity = new mongoose_1.Schema({
    // holds stubs
    // keys are TimeTag string + cityGUID
    key: { type: String, required: true, unique: true, index: true },
    citationStubs: [CitationStub],
    peopleCount: Number
});
//# sourceMappingURL=schema.js.map