/*
Provides read/write access to the read side database of the History Atlas

April 13th, 2021
*/

import { Broker } from './broker';
import { Config } from './config';
import { Database, QueryFunc } from './database';

interface APIReturn {
  NameTagGuids?: string[];
}

export type MessageHandler = APIHandler | EventHandler;
export type APIHandler = (msg: Buffer) => Promise<APIReturn>;
export type EventHandler = (msg: Buffer) => Promise<boolean>;

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

  private async startBroker(): Promise<void> {
    const isDBInitialized = await this.db.getDBStatus();
    this.broker = new Broker(this.conf, this.apiCallBack, this.eventCallBack, isDBInitialized)
  }

  private async apiCallBack(msg: Buffer): Promise<APIReturn> {

    // decode message
    const message = msg.toJSON();
    console.log('API got message ', message)

    const msgType = 'getNameTag';
    const queryFunc = this.db.queryMap.get(msgType) as QueryFunc;

    const result = await queryFunc('Bach')
    if (!result) {
      return {}
    }
    return {
      NameTagGuids: result.guid
    }
  }

  private async eventCallBack(msg: Buffer): Promise<boolean> {
    // view for incoming events from the persisted_event stream
    // also serves as the point of entry when replaying the event history
    // respond with true when event is processed for ack, 
    // or false for message to be nacked
    const message = JSON.parse(msg.toString())
    console.log(`event callback got message; `, message)
    return true;
  }
}

const rm = new ReadModel();
rm.db.connect()
rm.broker.connect()
