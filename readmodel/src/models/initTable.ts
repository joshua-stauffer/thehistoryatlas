/*
Model definition for initTable -- a special table which serves as a flag to rebuild the database.
*/

import mongoose, { Schema, Document } from 'mongoose';

export interface IInitTable extends Document {
    isInitialized: boolean;
}

const InitTable: Schema = new Schema({
    isInitialized: { type: Boolean, required: true, default: false }
})

export default mongoose.model<IInitTable>('InitTable', InitTable)
