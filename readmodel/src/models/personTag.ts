import { Schema, Document } from 'mongoose';


const PersonTag: Schema = new Schema({
    // lookup a person by guid
  
    guid: { type: String, index: true, required: true },
    names: [{ type: String }],
    orderedTimeTags: [{ type: String }]   // a list of time tag GUIDS representing chronological events
  })