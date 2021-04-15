/*
Model definition for documents TimeTagByPerson.

Stores citations with a combined key of time tag guid + person tag guid
*/

// NOTE: citation is the same here and in timeTagByCity. If you update one,
//          update the other too.

import mongoose, { Schema, Document } from 'mongoose';

export interface ITimeTagByPerson extends Document {
  key: string;
  citations: Citation[];
}

export interface Citation {
  guid: string;
  placeTags: string[];      // list of placeTag guids
  personTags: string[];     // list of person tag guids
  text: string;
  meta: CitationMetadata;
}

export interface CitationMetadata {
  author: string;
  publisher?: string;
  pubDate?: string;
  pageNum?: number;
}

const TimeTagByPerson: Schema = new Schema({

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
})

export default mongoose.model<ITimeTagByPerson>('TimeTagByPerson', TimeTagByPerson)
