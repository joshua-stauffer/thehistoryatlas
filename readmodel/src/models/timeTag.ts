/*
Model definition for document TimeTag
*/

import mongoose, { Schema, Document } from 'mongoose';

export interface ITimeTag extends Document {
  name: string;
  guid: string;
}

export enum TimeTagTypes {
  Range = "Year:Year",
  Year = "Year",
  Season = "Year:Quarter",
  Month = "Year:Month",
  Day = "Year:Month:Day"
}
  
const TimeTag: Schema = new Schema({
  // lookup a Time:
  // what names are associated with them?
  // which timetags are associated with them?

  guid: { type: String, index: true, required: true },
  type: TimeTagTypes,
})

export default mongoose.model<ITimeTag>('TimeTag', TimeTag)
