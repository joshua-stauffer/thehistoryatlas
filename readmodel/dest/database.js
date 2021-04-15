"use strict";
/*
Readside database interface for the History Atlas.
April 12, 2021
*/
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Database = void 0;
const mongoose_1 = __importDefault(require("mongoose"));
const initTable_1 = __importDefault(require("./models/initTable"));
const nameTag_1 = __importDefault(require("./models/nameTag"));
class Database {
    // private DB_TIMEOUT: number;
    // private DB_RETRY: number | null;
    constructor(conf) {
        // bindings
        this.getDBStatus = this.getDBStatus.bind(this);
        this.setDBStatus = this.setDBStatus.bind(this);
        const { DB_URI } = conf;
        this.DB_URI = DB_URI;
        this.DB_OPTIONS = { useUnifiedTopology: true, useNewUrlParser: true };
        // this.DB_TIMEOUT = DB_TIMEOUT;
        // this.DB_RETRY = DB_RETRY;
        // create query map and bind the methods to this object
        this.queryMap = new Map([
            ['GET_NAME_TAG', this.getNameTag.bind(this)] // () => this.get
        ]);
        this.mutatorMap = new Map([
            ['CREATE_NAME_TAG', this.createNameTag.bind(this)]
        ]);
        // try to reconnect if we lose connection
        //mongoose.connection.on('disconnected', this.connect)
    }
    async connect() {
        console.log('trying to connect to mongo with db_uri: ', this.DB_URI);
        try {
            mongoose_1.default.connect(this.DB_URI, this.DB_OPTIONS)
                .then(() => {
                console.log('successfully connected to MongoDB');
            });
        }
        catch (error) {
            console.log('got error: ', error);
        }
    }
    // Queries: for API use
    async getDBStatus() {
        /*
        Checks database for the InitTable.
    
        Returns true if it finds it, else drops all collections from the database
        and returns false.
        */
        const flag = initTable_1.default.findOne();
        if (flag) {
            // yay database already exists!
            return true;
        }
        else {
            // gotta rebuild it - but first, make sure it's empty
            const collections = await mongoose_1.default.connection.db.collections();
            for (const c of collections) {
                await c.drop();
            }
            return false;
        }
    }
    async setDBStatus() {
        /*
        Sets the database InitTable.
    
        After database is (re)built, call this method to ensure that next time the
        application restarts the data will be preserved.
        */
        await initTable_1.default.create({ isInitialized: true });
    }
    async getNameTag(name) {
        // returns all GUIDs associated with a given name
        return await nameTag_1.default.findOne({
            name: name
        }, (err, doc) => {
            if (err) {
                console.log('error in getNameTag was ', err);
            }
            else {
                console.log('got doc in getNameTag! ', doc);
            }
        });
    }
    // Mutations: to be used by persistedEvent-handlers only
    async createNameTag(payload) {
        // create a new instance of a NameTag
        const { name, guid } = payload;
        nameTag_1.default.create({
            name: name,
            guid: [guid]
        }, (err, doc) => {
            if (err) {
                console.log('error in createNameTag was ', err);
            }
            else {
                console.log('got doc in createNameTAg! ', doc);
            }
        });
    }
    async addToNameTag(payload) {
        // add a guid to an existing NameTag entry
        const { name, guid } = payload;
        nameTag_1.default.updateOne({ name: name }, { $push: { guid: guid } });
    }
    async delNameTag(name) {
        // removes a document from the table
        await nameTag_1.default.findOneAndDelete({
            name: name
        });
    }
}
exports.Database = Database;
//# sourceMappingURL=database.js.map