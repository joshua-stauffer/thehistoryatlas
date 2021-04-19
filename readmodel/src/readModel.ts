/*
Provides read/write access to the read side database of the History Atlas

April 13th, 2021
*/

import { Broker } from './broker';
import { Config } from './config';
import { Database, QueryFunc, MutatorFunc } from './database';

export interface Message {
  type: string;
  payload: any;
}

export interface APIRequest {
  type: string;
  payload: any;
}

export interface EventRequest {
  type: string;
  payload: any;
}

export type MessageHandler = APIHandler | EventHandler;
export type APIHandler = (msg: APIRequest) => Promise<Message>;
export type EventHandler = (msg: EventRequest) => Promise<boolean>;

class ReadModel {

  broker?: Broker;
  conf: Config;
  db: Database;


  constructor() {
    // take care of bindings
    this.apiCallBack = this.apiCallBack.bind(this);
    this.eventCallBack = this.eventCallBack.bind(this);
    this.startBroker = this.startBroker.bind(this);

    this.conf = new Config();
    this.db = new Database(this.conf)
  }

  async runForever(): Promise<void> {
    /* 
    Initializes database and connects to RabbitMQ.
    Will continue listening for messages until an error or stopped.  
    */

    await this.db.connect();
    await this.startBroker();
  }

  private async startBroker(): Promise<void> {
    /* 
    Asynchronously starts the broker.
    */

    const isDBInitialized = await this.db.getDBStatus();
    this.broker = new Broker(this.conf, this.apiCallBack, this.eventCallBack, isDBInitialized);
    await this.broker.connect();
    if (!isDBInitialized) {
      // passing a false isDBInitialized value to the broker constructor ^ will 
      // automatically trigger an event history replay. All we need to do here 
      // is update the database so that next time we don't need to request a replay.
      // what are we doing if for some reason the history replay fails?
      await this.db.setDBStatus()
    }
  }

  async apiCallBack(msg: APIRequest): Promise<Message> {
    /*
    Point of contact for the api exchange.
    Incoming messages are treated exclusively as queries, and are passed to a
    database query function for processing.
    */

    console.log(`ReadModel.apiCallBack: received message ${msg}`)

    const { type, payload } = msg;
    const queryFunc = this.db.queryMap.get(type) as QueryFunc;
    if (!queryFunc) {
      console.error(`Unknown type ${type} passed to ReadModel API callback. Discarding and doing nothing.`)
      return {
        type: "ERROR",
        payload: {
          message: `Unknown type ${type} passed to ReadModel API`
        }
      }
    }

    const result = await queryFunc(payload)
    if (!result) {
      console.warn(`ReadModel.apiCallBack: payload ${payload} returned no results. Discarding and doing nothing.`)
      return {
        type: "QUERY_RESPONSE",
        payload: {result: null}
      }
    } else {
      return {
        type: "QUERY_RESPONSE",
        payload: result
      }
    }
  }

  private async eventCallBack(msg: APIRequest): Promise<boolean> {
    /*
    Point of contact for the persisted_events exchange.
    Incoming messages are treated exclusively as mutations, and are passed to a 
    database mutation function for processing.
    */

    console.log(`ReadModel.eventCallBack: received message ${msg}`)
    const { type, payload } = msg;
    const mutatorFunc = this.db.mutatorMap.get(type) as MutatorFunc;

    if (!mutatorFunc) {
      console.error(`Unknown type ${type} passed to ReadModel API callback. Discarding and doing nothing.`)
      return false
    }

    await mutatorFunc(payload) // would be nice to get a value back here to indicate a successful operation
    return true
  }
}

console.log('running read model')
const rm = new ReadModel();
rm.runForever()
console.log('should be running')