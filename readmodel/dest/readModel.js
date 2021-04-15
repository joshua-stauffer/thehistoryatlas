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
        /*
        Asynchronously starts the broker.
        */
        const isDBInitialized = await this.db.getDBStatus();
        this.broker = new broker_1.Broker(this.conf, this.apiCallBack, this.eventCallBack, isDBInitialized);
        await this.broker.connect();
        if (!isDBInitialized) {
            // passing a false isDBInitialized value to the broker constructor ^ will 
            // automatically trigger an event history replay. All we need to do here 
            // is update the database so that next time we don't need to request a replay.
            // what are we doing if for some reason the history replay fails?
            await this.db.setDBStatus();
        }
    }
    async apiCallBack(msg) {
        /*
        Point of contact for the api exchange.
        Incoming messages are treated exclusively as queries, and are passed to a
        database query function for processing.
        */
        console.log(`ReadModel.apiCallBack: received message ${msg}`);
        const { type, payload } = msg;
        const queryFunc = this.db.queryMap.get(type);
        if (!queryFunc) {
            console.error(`Unknown type ${type} passed to ReadModel API callback. Discarding and doing nothing.`);
            return {
                type: "ERROR",
                payload: {
                    message: `Unknown type ${type} passed to ReadModel API`
                }
            };
        }
        const result = await queryFunc(payload);
        if (!result) {
            console.warn(`ReadModel.apiCallBack: payload ${payload} returned no results. Discarding and doing nothing.`);
            return {
                type: "QUERY_RESPONSE",
                payload: { result: null }
            };
        }
        else {
            return {
                type: "QUERY_RESPONSE",
                payload: { result: result }
            };
        }
    }
    async eventCallBack(msg) {
        /*
        Point of contact for the persisted_events exchange.
        Incoming messages are treated exclusively as mutations, and are passed to a
        database mutation function for processing.
        */
        console.log(`ReadModel.eventCallBack: received message ${msg}`);
        const { type, payload } = msg;
        const mutatorFunc = this.db.mutatorMap.get(type);
        if (!mutatorFunc) {
            console.error(`Unknown type ${type} passed to ReadModel API callback. Discarding and doing nothing.`);
            return false;
        }
        await mutatorFunc(payload); // would be nice to get a value back here to indicate a successful operation
        return true;
    }
}
const rm = new ReadModel();
rm.runForever();
//# sourceMappingURL=readModel.js.map