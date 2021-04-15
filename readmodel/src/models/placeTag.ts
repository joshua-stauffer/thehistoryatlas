/*
Model definition for document PlaceTag
*/

import mongoose, { Schema, Document } from 'mongoose';

export interface IPlaceTag extends Document {
  guid: string;
  names: string[];
  location: Location;
}

export enum CoordType {
  POINT = "Point",
  REGION = "Region"
}

const Point: Schema = new Schema({
  latitude: Number,
  longitude: Number
})

const Location: Schema = new Schema({
  type: CoordType,
  point: Point,       // even shapes should have this referencing their 'center'
  shape: [ Point ]
})

const PlaceTag: Schema = new Schema({
  // get a city's names and location

  guid: { type: String, index: true, required: true },
  names: [{ type: String }],
  location: Location
})

export default mongoose.model<IPlaceTag>('PlaceTag', PlaceTag)
