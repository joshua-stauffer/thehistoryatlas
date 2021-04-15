"use strict";
/*
Provides read/write access to the read side database of the History Atlas

April 13th, 2021
*/
Object.defineProperty(exports, "__esModule", { value: true });
const broker_1 = require("./broker");
const config_1 = require("./config");
const database_1 = require("./database");
class ReadModel {
    constructor() {
        // take care of bindings
        this.apiCallBack = this.apiCallBack.bind(this);
        this.eventCallBack = this.eventCallBack.bind(this);
        this.startBroker = this.startBroker.bind(this);
        this.conf = new config_1.Config();
        this.db = new database_1.Database(this.conf);
    }
    async runForever() {
        /*
        Initializes database and connects to RabbitMQ.
        Will continue listening for messages until an error or stopped.
        */
        await this.db.connect();
        await this.startBroker();
    }
    async startBroker() {
        // Essentially an asynchronous constructor method for the broker
        const isDBInitialized = await this.db.getDBStatus();
        this.broker = new broker_1.Broker(this.conf, this.apiCallBack, this.eventCallBack, isDBInitialized);
        await this.broker.connect();
        if (!isDBInitialized) {
            // what are we doing if for some reason the history replay fails?
            await this.db.setDBStatus();
        }
    }
    async apiCallBack(msg) {
        // decode message
        const message = msg.toJSON();
        console.log('API got message ', message);
        const msgType = 'getNameTag';
        const queryFunc = this.db.queryMap.get(msgType);
        const result = await queryFunc('Bach');
        if (!result) {
            return {};
        }
        return {
            NameTagGuids: result.guid
        };
    }
    async eventCallBack(msg) {
        // view for incoming events from the persisted_event stream
        // also serves as the point of entry when replaying the event history
        // respond with true when event is processed for ack, 
        // or false for message to be nacked
        const message = JSON.parse(msg.toString());
        console.log(`event callback got message; `, message);
        return true;
    }
}
const rm = new ReadModel();
rm.runForever();
//# sourceMappingURL=readModel.js.map