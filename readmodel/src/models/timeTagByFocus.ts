// Model definition for TimeTagByFocus, a core structure used by the API and client

import mongoose, { Schema, Document } from 'mongoose';
import { DB } from '../types';

export interface ITimeTagByFocus extends Document {
  key: string;
  citations: DB.Citation[];
}

const TimeTagByFocus: Schema = new Schema({

  key: { type: String, index: true, required: true, unique: true },
  citations: { 
    GUID: String,
    tags: [{
      type: String,
      GUID: String,
      start: Number,
      end: Number
    }],
    text: String,
    meta: {
      author: String,
      publisher: String,
      pubDate: String,
      pageNum: Number
    }
   }
})
export default mongoose.model<ITimeTagByFocus>('TimeTagByFocus', TimeTagByFocus)
