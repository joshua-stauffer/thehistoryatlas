"use strict";
/*
A class to handle config based on env variables
*/
Object.defineProperty(exports, "__esModule", { value: true });
exports.Config = void 0;
class Config {
    constructor() {
        this.TESTING = this.getBool("TESTING");
        this.CONFIG = this.getString("CONFIG");
        this.NETWORK_HOST_NAME = this.getString("HOST_NAME", "localhost");
        this.BROKER_USERNAME = this.getString("BROKER_USERNAME", "guest");
        this.BROKER_PASS = this.getString("BROKER_PASS", "guest");
        this.DB_USERNAME = this.getString("DB_USERNAME");
        this.DB_PASS = this.getString("DB_PASS");
        this.RECV_QUEUE = this.getString("RECV_QUEUE");
        this.SEND_QUEUE = this.getString("SEND_QUEUE");
        this._DEV_DB_URI = this.getString("DEV_DB_URI");
        this._TESTING_DB_URI = this.getString("TESTING_DB_URI");
        this._PROD_DB_URI = this.getString("PROD_DB_URI");
        this.DB_URI = this.getDB();
        this.DB_OPTIONS = {};
        this.DB_TIMEOUT = this.getNum("DB_TIMEOUT", 5000);
        this.DB_RETRY = this.getNumOrNull("DB_RETRY", null);
    }
    getString(val, fallback = "") {
        // get a string from the environment
        const envVal = process.env[val];
        if (typeof envVal === "string") {
            return envVal;
        }
        return fallback;
    }
    getBool(val, fallback = false) {
        // get a bool from the environment
        const envVal = process.env[val];
        if (envVal === "true" || envVal === "True") {
            return true;
        }
        else if (envVal === "false" || envVal === "False") {
            return false;
        }
        // not set
        return fallback;
    }
    getNum(val, fallback = 0) {
        // get a number from the environment
        const envVal = process.env[val];
        try {
            return Number(envVal);
        }
        catch (error) {
            console.log(`Config is setting default number for val ${val}`);
            return fallback;
        }
    }
    getNumOrNull(val, fallback = 0) {
        // get a number from the environment
        // currently supports null for the sake of DB_RETRY
        // ... but if this gets cumbersome, could be broken out into its own method
        const envVal = process.env[val];
        if (envVal === "null") {
            return null;
        }
        try {
            return Number(envVal);
        }
        catch (error) {
            console.log(`Config is setting default value for val ${val}`);
            return fallback;
        }
    }
    getDB() {
        // sets the public DB_URI to the correct uri val based on CONFIG
        switch (this.CONFIG) {
            case "PRODUCTION":
                return this._PROD_DB_URI;
            case "TESTING":
                return this._TESTING_DB_URI;
            default:
                return this._DEV_DB_URI;
        }
    }
}
exports.Config = Config;
//# sourceMappingURL=config.js.map