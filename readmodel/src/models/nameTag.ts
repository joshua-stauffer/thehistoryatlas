/*
Model definition for document NameTag
*/

import mongoose, { Schema, Document } from 'mongoose';


export interface INameTag extends Document {
  name: string;
  guid: string[];
}
  
const NameTag: Schema = new Schema({
  // lookup a name: who is it associated with?
  // should i include places here or break it out into its own?

  name: { type: String, required: true, index: true },
  guid: [{ type: String }],   // each name might have many people
})



export default mongoose.model<INameTag>('NameTag', NameTag)
