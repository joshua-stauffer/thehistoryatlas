/*
Readside database interface for the History Atlas.
April 12, 2021
*/

import mongoose from 'mongoose';
import InitTable from './models/initTable';
import NameTag, { INameTag } from './models/nameTag';
import FocusSummary, { IFocusSummary } from './models/focusSummary';
import { Config, DB_OPTIONS } from './config';



export type QueryFunc = (payload: QueryPayload) => Promise<QueryResponse | null>;
export type MutatorFunc = (payload: MutatorPayload) => Promise<void>;

type FocusType = "PERSON" | "PLACE" | "TIME";

interface QueryPayload {
  focusType?: FocusType;
  GUID?: string;
  name?: string; // deprecate this?
}
type QueryResponse = 
  INameTag | IFocusSummary;

// mutator payload types
type MutatorPayload = 
  CreateNameTagPayload
  | AddToNameTagPayload;

interface CreateNameTagPayload {
  name: string;
  guid: string
}
interface AddToNameTagPayload {
  name: string;
  guid: string
}


export class Database {

  queryMap: Map<string, QueryFunc>
  mutatorMap: Map<string, MutatorFunc>

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
      //['GET_NAME_TAG', this.getNameTag.bind(this)], // including this causes the compiler to crash?!
      ['GET_FOCUS_SUMMARY', this.getFocusSummary.bind(this)]
    ])
    this.mutatorMap = new Map([
      ['CREATE_NAME_TAG', this.createNameTag.bind(this)]
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

  async setDBStatus(): Promise<void> {
    /* 
    Sets the database InitTable.

    After database is (re)built, call this method to ensure that next time the
    application restarts the data will be preserved.
    */
    
    await InitTable.create({ isInitialized: true })
  }

  private async getNameTag({ name }: QueryPayload): Promise<INameTag | null> {
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

  private async getFocusSummary({ focusType, GUID }: QueryPayload): Promise<IFocusSummary | null> {
    // Primary way to obtain overview of a given focus.
    // Contains enough data to find all other data linked to this entity.
    if (!(focusType && GUID)) throw new Error('Incorrect arguments passed to getFocusSummary')
    switch (focusType) {

      case "PERSON":
        return {
          GUID: 'bach-some-guid',
          timeTagSummaries: [
            {
              timeTag: '1685',
              GUID: '1685-guid-1234',
              citationCount: 1
            },
            {
              timeTag: '1703',
              GUID: '1703-guid-1234',
              citationCount: 3
            },
            {
              timeTag: '1750:3:7:28',
              GUID: '1750-guid-1234',
              citationCount: 2
            }
          ]
        } as IFocusSummary;
      case "PLACE":
        return {
          GUID: 'bach-some-guid',
          timeTagSummaries: [
            {
              timeTag: '1685',
              GUID: '1685-guid-1234',
              citationCount: 1
            },
            {
              timeTag: '1703',
              GUID: '1703-guid-1234',
              citationCount: 3
            },
            {
              timeTag: '1750:3:7:28',
              GUID: '1750-guid-1234',
              citationCount: 2
            }
          ]
        } as IFocusSummary;

      case "TIME":
        return {
          GUID: 'bach-some-guid',
          timeTagSummaries: [
            {
              timeTag: '1685',
              GUID: '1685-guid-1234',
              citationCount: 1
            },
            {
              timeTag: '1703',
              GUID: '1703-guid-1234',
              citationCount: 3
            },
            {
              timeTag: '1750:3:7:28',
              GUID: '1750-guid-1234',
              citationCount: 2
            }
          ]
        } as IFocusSummary;

      default:
        throw new Error('Unknown focusType passed to getFocusSummary')
    }
  }


  // Mutations: to be used by persistedEvent-handlers only



  async createNameTag(payload: CreateNameTagPayload): Promise<void> {
    // create a new instance of a NameTag
    
    const { name, guid } = payload;

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

  async addToNameTag(payload: AddToNameTagPayload): Promise<void> {
    // add a guid to an existing NameTag entry

    const { name, guid } = payload;

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
