// Model definition for documents TimeTagByPerson.
// Stores references to a single entity

import mongoose, { Schema, Document } from 'mongoose';
import { DB } from '../types';

export interface IFocusSummary extends Document {
  GUID: string;
  timeTagSummaries: DB.TimeTagSummary[];
}

const FocusSummary: Schema = new Schema({
  GUID: { type: String, index: true, required: true, unique: true },
  timeTagSummaries: [{
    timeTag: String,
    GUID: String,
    citationCount: Number
  }]
})

export default mongoose.model<IFocusSummary>('FocusSummary', FocusSummary);
