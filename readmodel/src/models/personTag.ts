/*
Model definition for document PersonTag
*/

import mongoose, { Schema, Document } from 'mongoose';

export interface IPersonTag extends Document {
  guid: string;
  names: string[];
  orderedTimeTags: string[]
}
  
const PersonTag: Schema = new Schema({
  // lookup a person:
  // what names are associated with them?
  // which timetags are associated with them?

  guid: { type: String, index: true, required: true },
  names: [{ type: String }],
  orderedTimeTags: [{ type: String }]   // a list of time tag GUIDS representing chronological events
})

export default mongoose.model<IPersonTag>('PersonTag', PersonTag)
