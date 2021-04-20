// Model definition for associating tags with names

import mongoose, { Schema, Document } from 'mongoose';
export interface ITag extends Document {
  GUID: string;
  names: string[];
  // other useful things?
}

const Tag: Schema = new Schema({
  GUID: { type: String, required: true, index: true },
  names: [String],
})

export default mongoose.model<ITag>('Tag', Tag);
