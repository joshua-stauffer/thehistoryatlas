/*
Readside database interface for the History Atlas.
April 12, 2021
*/

import mongoose from 'mongoose';
import InitTable from './models/initTable';
import NameTag, { INameTag } from './models/nameTag';
import Tag, { ITag } from './models/tags';
import FocusSummary, { IFocusSummary } from './models/focusSummary';
import { Config, DB_OPTIONS } from './config';
import { APITypes, DB } from './types';
import { v4 } from 'uuid';


export type QueryFunc = (payload: any) => Promise<any>;
export type MutatorFunc = (payload: MutatorPayload) => Promise<void>;

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
      ['GET_FOCUS_SUMMARY', this.getFocusSummary.bind(this)],
      ['GET_TIME_TAG_DETAILS', this.getTimeTagDetails.bind(this)],
      ['SEARCH_FOCUS_BY_NAME', this.searchFocusByName.bind(this)]
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

  private async getNameTag({ name }: APITypes.NameTagQuery): Promise<INameTag | null> {
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

  private async getFocusSummary(
    { focusType, GUID }: APITypes.FocusSummaryQuery
    ): Promise<APITypes.FocusSummaryResponse> {
    // Primary way to obtain overview of a given focus.
    // Contains enough data to find all other data linked to this entity.
    if (!(focusType && GUID)) throw new Error('Incorrect arguments passed to getFocusSummary')
    let payload = null;

    switch (focusType) {

      case "PERSON":
        payload = {
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
        break;

      case "PLACE":
        payload = {
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
        break;

      case "TIME":
        payload = {
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
        break;
        
      default:
        throw new Error('Unknown focusType passed to getFocusSummary')
    }

    return {
      type: 'FOCUS_SUMMARY',
      payload: payload
    }
  }

  private async getTimeTagDetails(
    { focusGUID, timeTagGUID }: APITypes.TimeTagDetailsQuery
    ): Promise<APITypes.TimeTagDetailsResponse> {
    // Primary way to obtain overview of a given focus.
    // Contains enough data to find all other data linked to this entity.
    if (!( focusGUID && timeTagGUID )) throw new Error('Incorrect arguments passed to getFocusSummary')
    let payload = {};
    
    return {
      type: 'TIME_TAG_DETAILS',
      payload:   {
        citations: [
          {
            GUID: 'citation-guid-2844',
            text: 'Sometime around here buxtehude was born',
            tags: [
              {
                type: 'PERSON',
                GUID: v4(),
                start: 23,
                end: 29
              }
            ],
            meta: {
              author: "someone",
              publisher: "a publisher"
            }
          }
        ]
      }
    }
  }

  async searchFocusByName(
    { focusType, searchTerm }: APITypes.SearchFocusByNameQuery
  ): Promise<APITypes.SearchFocusByNameResponse> {
    if (!(focusType && searchTerm)) throw new Error('Incorrect arguments passed to searchFocusByName')
    const results = await NameTag.findOne({ name: searchTerm }, 'GUIDs').exec() as unknown as string[]; // this is stupid..
    if (!results) return {
      type: 'SEARCH_FOCUS_BY_NAME',
      payload: {
        focuses: []
      }
    }
    const tags = results.map(async (GUID: string) => await Tag.findOne({GUID: GUID}));
    if (!tags) return {
      type: 'SEARCH_FOCUS_BY_NAME',
      payload: {
        focuses: []
      }
    }
    const r = {
      type: 'SEARCH_FOCUS_BY_NAME',
      payload: {
        focuses: tags
      }
    }
    console.log('searchFocusByName is returning ', r)
    return r
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
