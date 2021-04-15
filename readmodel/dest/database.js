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
const nameTag_1 = __importDefault(require("./models/nameTag"));
class Database {
    // private DB_TIMEOUT: number;
    // private DB_RETRY: number | null;
    constructor(conf) {
        const { DB_URI } = conf;
        this.DB_URI = DB_URI;
        this.DB_OPTIONS = { useUnifiedTopology: true, useNewUrlParser: true };
        // this.DB_TIMEOUT = DB_TIMEOUT;
        // this.DB_RETRY = DB_RETRY;
        // create query map and bind the methods to this object
        this.queryMap = new Map([
            ['getNameTag', this.getNameTag.bind(this)]
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
    async createNameTag(name, guid) {
        // create a new instance of a NameTag
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
    async addToNameTag(name, guid) {
        // add a guid to an existing NameTag entry
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
/*
    if (!this.DB_RETRY) {

      while (true) {
        try {
          await mongoose.connect(this.DB_URI, this.DB_OPTIONS)
          console.log('successfully connected to mongo!')
          break
        } catch (error) {
          console.log(`Can't connect to Mongo: ${error} Trying again infinitely.`)
          const setTimeoutPromise = util.promisify(setTimeout);
          await setTimeoutPromise(this.DB_TIMEOUT);
          break
        }
      }

    } else { // try conf.DB_RETRY amount of times
      let tries = this.DB_RETRY;
      while (tries > 0) {
        try {
          await mongoose.connect(this.DB_URI, this.DB_OPTIONS)
        } catch (error) {
          tries--;
          console.log(`Can't connect to Mongo: ${error} Trying ${tries} more times.`)
          const setTimeoutPromise = util.promisify(setTimeout);
          await setTimeoutPromise(this.DB_TIMEOUT);
        }
      }
    }
  }
*/ 
//# sourceMappingURL=database.js.map