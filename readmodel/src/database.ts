/*
Readside database interface for the History Atlas.
April 12, 2021
*/

import mongoose from 'mongoose';
import InitTable from './models/initTable';
import NameTag, { INameTag } from './models/nameTag';
import { Config, DB_OPTIONS } from './config';

type QueryResponse = 
  INameTag | null;

export type QueryFunc = (param: string) => Promise<QueryResponse>;

export class Database {

  queryMap: Map<string, QueryFunc>

  private DB_OPTIONS: DB_OPTIONS;
  private DB_URI: string;
  // private DB_TIMEOUT: number;
  // private DB_RETRY: number | null;

  constructor(conf: Config) {
    // bindings
    this.getDBStatus = this.getDBStatus.bind(this);
    this.setDBStatus = this.setDBStatus.bind(this);

    const { DB_URI } = conf;
    this.DB_URI = DB_URI
    this.DB_OPTIONS = { useUnifiedTopology: true, useNewUrlParser: true }
    // this.DB_TIMEOUT = DB_TIMEOUT;
    // this.DB_RETRY = DB_RETRY;

    // create query map and bind the methods to this object
    this.queryMap = new Map([
      ['getNameTag', this.getNameTag.bind(this)]
    ])

    // try to reconnect if we lose connection
    //mongoose.connection.on('disconnected', this.connect)
  }

  async connect(): Promise<void> {
    console.log('trying to connect to mongo with db_uri: ', this.DB_URI)
    try {
      mongoose.connect(this.DB_URI, this.DB_OPTIONS)
        .then(() => {
          console.log('successfully connected to MongoDB')
          }
        )
    } catch (error) {
      console.log('got error: ', error)
    }
  }
  // Queries: for API use

  async getDBStatus(): Promise<boolean> {
    /* 
    Checks database for the InitTable.

    Returns true if it finds it, else drops all collections from the database
    and returns false.
    */
    const flag = InitTable.findOne();
    if (flag) {
      // yay database already exists!
      return true;
    } else {
      // gotta rebuild it - but first, make sure it's empty
      const collections = await mongoose.connection.db.collections()
      for (const c of collections) {
        await c.drop();
      }
      return false;
    }
  }

  private async setDBStatus(): Promise<void> {
    /* 
    Sets the database InitTable.

    After database is (re)built, call this method to ensure that next time the
    application restarts the data will be preserved.
    */
    
    await InitTable.create({ isInitialized: true })
  }

  private async getNameTag(name: string): Promise<INameTag | null> {
    // returns all GUIDs associated with a given name
    
    return await NameTag.findOne({
      name: name
    }, (err: mongoose.CallbackError, doc: INameTag | null): void  => {
      if (err) {
        console.log('error in getNameTag was ', err)
      } else {
        console.log('got doc in getNameTag! ', doc)
      }

    })

  }


  // Mutations: to be used by persistedEvent-handlers only

  async createNameTag(name: string, guid: string): Promise<void> {
    // create a new instance of a NameTag
    
    NameTag.create({
      name: name,
      guid: [guid]
    }, (err: mongoose.CallbackError, doc: INameTag | null): void  => {
      if (err) {
        console.log('error in createNameTag was ', err)
      } else {
        console.log('got doc in createNameTAg! ', doc)
      }
    })
  }

  async addToNameTag(name: string, guid: string): Promise<void> {
    // add a guid to an existing NameTag entry

    NameTag.updateOne(
      { name: name },
      { $push: { guid: guid }},
    );

  }

  async delNameTag(name: string): Promise<void> {
    // removes a document from the table

    await NameTag.findOneAndDelete({
      name: name
    })
  }

}
