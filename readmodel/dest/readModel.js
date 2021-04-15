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
        this.conf = new config_1.Config();
        this.db = new database_1.Database(this.conf);
        this.broker = new broker_1.Broker(this.conf, this.apiCallBack, this.eventCallBack);
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
        console.log(`event callback got message; `, msg);
        return true;
    }
}
const rm = new ReadModel();
rm.db.connect();
rm.broker.connect();
//# sourceMappingURL=readModel.js.map