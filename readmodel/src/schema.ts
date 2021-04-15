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

import { Schema, Document } from 'mongoose';



export const TimeTag: Schema = new Schema({
  // lookup a timetag -- does it exist yet?

  val: { type: String, index: true },
  GUID: { type: String, required: true, unique: true }
})

// Time Tags by Person

const CitationMeta: Schema = new Schema({
  // holds citation metadata

  author: [{ type: String }],
  publisher: { type: String},
  pubDate: { type: Date },
  pageNumber: { type: Number }
})

const Citation: Schema = new Schema({
  // subdoc for holding a single citation

  contributor: { type: String },
  text: { type: String },
  meta: CitationMeta,
  // tags
  personTags: [{ type: String }] // guids
})

export const TimeTagByPerson: Schema = new Schema({
  // primary holder for citations
  // keys are TimeTag string + personGUID

  key: { type: String, required: true, unique: true, index: true },
  citations: [ Citation ]
})

// Time Tags by City 

const CitationStub: Schema = new Schema({
  personGUIDS: [{ type: String }]
})

export const TimeTagByCity: Schema = new Schema({
  // holds stubs
  // keys are TimeTag string + cityGUID

  key: { type: String, required: true, unique: true, index: true },
  citationStubs: [ CitationStub ],
  peopleCount: Number
})

