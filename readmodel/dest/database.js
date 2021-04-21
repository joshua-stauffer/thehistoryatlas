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
const tags_1 = __importDefault(require("./models/tags"));
const uuid_1 = require("uuid");
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
            //['GET_NAME_TAG', this.getNameTag.bind(this)], // including this causes the compiler to crash?!
            ['GET_FOCUS_SUMMARY', this.getFocusSummary.bind(this)],
            ['GET_TIME_TAG_DETAILS', this.getTimeTagDetails.bind(this)],
            ['SEARCH_FOCUS_BY_NAME', this.searchFocusByName.bind(this)]
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
            console.log('retrying MongoDB connection in 0.5 seconds');
            setTimeout(this.connect, 500);
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
    async getNameTag({ name }) {
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
    async getFocusSummary({ focusType, GUID }) {
        // Primary way to obtain overview of a given focus.
        // Contains enough data to find all other data linked to this entity.
        if (!(focusType && GUID))
            throw new Error('Incorrect arguments passed to getFocusSummary');
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
                };
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
                };
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
                };
                break;
            default:
                throw new Error('Unknown focusType passed to getFocusSummary');
        }
        return {
            type: 'FOCUS_SUMMARY',
            payload: payload
        };
    }
    async getTimeTagDetails({ focusGUID, timeTagGUID }) {
        // Primary way to obtain overview of a given focus.
        // Contains enough data to find all other data linked to this entity.
        if (!(focusGUID && timeTagGUID))
            throw new Error('Incorrect arguments passed to getFocusSummary');
        let payload = {};
        return {
            type: 'TIME_TAG_DETAILS',
            payload: {
                citations: [
                    {
                        GUID: 'citation-guid-2844',
                        text: 'Sometime around here buxtehude was born',
                        tags: [
                            {
                                type: 'PERSON',
                                GUID: uuid_1.v4(),
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
        };
    }
    async searchFocusByName({ focusType, searchTerm }) {
        if (!(focusType && searchTerm))
            throw new Error('Incorrect arguments passed to searchFocusByName');
        const results = await nameTag_1.default.findOne({ name: searchTerm }, 'GUIDs').exec(); // this is stupid..
        if (!results)
            return {
                type: 'SEARCH_FOCUS_BY_NAME',
                payload: {
                    focuses: []
                }
            };
        const tags = results.map(async (GUID) => await tags_1.default.findOne({ GUID: GUID }));
        if (!tags)
            return {
                type: 'SEARCH_FOCUS_BY_NAME',
                payload: {
                    focuses: []
                }
            };
        const r = {
            type: 'SEARCH_FOCUS_BY_NAME',
            payload: {
                focuses: tags
            }
        };
        console.log('searchFocusByName is returning ', r);
        return r;
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