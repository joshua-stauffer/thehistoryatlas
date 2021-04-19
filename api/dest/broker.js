"use strict";
/*
RabbitMQ broker for the History Atlas Apollo GraphQL API.

April 16th 2021
*/
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Broker = void 0;
const Amqp = __importStar(require("amqplib"));
const uuid_1 = require("uuid");
class Broker {
    constructor(config) {
        this.onConnectionClosed = () => {
            // handle the connection being closed unexpected, and try to reconnect.
            console.log('connection was closed');
        };
        this.onConnectionError = (err) => {
            // handle an error on the connection.
            // error is called if the server emits 'error': an operation failed due to a failed
            // precondition, or an admin closed the channel manually.
            // this won't be called if the connection closes with an error.
            console.error(`error in connection ${err}`);
        };
        this.onConnectionReturn = (msg) => {
            // this gets called if a message is published as mandatory and the recipient
            // can't be found. 
            console.warn(`message was returned: ${msg}`);
        };
        this.onConnectionDrain = () => {
            // if a connection has returned false from .publish or .sendToQueue, it will emit
            // 'drain' after it's ready for writes again.
            console.log('drained');
        };
        this.openChannel = (conn) => {
            // open a new channel
            console.log('Opening a new primary channel.');
            conn.createChannel()
                .then(channel => {
                // save channel for later
                this.channel = channel;
                // set event listeners
                channel.on('close', this.onConnectionClosed);
                channel.on('error', (err) => this.onConnectionError(err));
                channel.on('return', this.onConnectionReturn);
                channel.on('drain', this.onConnectionDrain);
                this.declareExchanges(channel);
            }).catch((err) => {
                console.log('Error while opening channel: ', err);
            });
        };
        this.declareExchanges = (channel) => {
            // Ensure that the exchange exists. if it does and we supply different arguments,
            // the channel will be closed.
            for (let exchConf of this.exchanges) {
                channel.assertExchange(exchConf.name, exchConf.type)
                    .then(() => {
                    this.createQueue(channel, exchConf);
                }).catch((err) => {
                    console.log(`Caught error ${err} while declaring exchange ${exchConf.name}.`);
                });
            }
        };
        this.createQueue = (channel, exchConf) => {
            // create a queue
            channel.assertQueue(exchConf.queueName, exchConf.queueOptions)
                .then((ok) => {
                exchConf.queueName = ok.queue;
                this.bindQueue(channel, exchConf);
            }).catch((err) => {
                console.log(`Got error ${err} while creating queue ${exchConf.queueName}`);
            });
        };
        this.bindQueue = (channel, exchConf) => {
            // bind a queue to an exchange
            const { queueName, name, pattern } = exchConf;
            channel.bindQueue(queueName, name, pattern)
                .then(() => {
                this.startListening(channel, exchConf);
            }).catch((err) => {
                console.log(`Got error ${err} while binding queue ${queueName} to ${name}`);
            });
        };
        this.startListening = (channel, exchConf) => {
            // start consuming on an exchange
            const { queueName, callBack, consumeOptions } = exchConf;
            channel.consume('amq.rabbitmq.reply-to', // setting this manually for now
            callBack, consumeOptions)
                .then((ok) => {
                exchConf.consumerTag = ok.consumerTag;
                console.log('Ready to receive messages at queue ', queueName);
            });
        };
        this.connect = this.connect.bind(this);
        this.queryReadModel = this.queryReadModel.bind(this);
        this.connect.bind(this);
        this.openChannel.bind(this);
        this.queryMap = new Map();
        const { BROKER_PASS, BROKER_USERNAME, NETWORK_HOST_NAME } = config;
        this.config = {
            protocol: 'amqp',
            hostname: NETWORK_HOST_NAME,
            port: 5672,
            username: BROKER_USERNAME,
            password: BROKER_PASS,
            vhost: '/',
        };
        this.exchanges = [{
                // This exchange can be used for any non-essential query
                // RPC operations. Anything requiring delivery confirmation
                // (like Commands) should probably a more reliable exchange.
                name: 'api',
                type: 'topic',
                queueName: '',
                pattern: 'request.readmodel',
                callBack: this.handleRPCCallback.bind(this),
                consumeOptions: {
                    noAck: true,
                    exclusive: true,
                    durable: false,
                },
                exchangeOptions: {
                    durable: false
                }
            },
            // we can add additional exchanges here, if need be
        ];
    }
    publishRPC(msg, recipient, exchangeName) {
        if (!this.channel)
            throw new Error('Channel doesn\'t exist');
        const exchange = this.exchanges.find(ex => ex.name === exchangeName);
        const queryID = uuid_1.v4();
        if (!this.channel.publish(exchange.name, recipient, Buffer.from(JSON.stringify(msg)), {
            replyTo: 'amq.rabbitmq.reply-to',
            correlationId: queryID
        }))
            throw new Error('Stream is full. Try again after receiving "drain" event.');
        return new Promise((resolve, reject) => {
            this.queryMap.set(queryID, {
                resolve: resolve, reject: reject
            });
        });
    }
    async queryReadModel(msg) {
        // accepts a json message and publishes it.
        return this.publishRPC(msg, 'request.readmodel', 'api');
    }
    async handleRPCCallback(msg) {
        // This callback is passed to the Amqp.consume method, and will be invoked
        // whenever a message is received.
        console.log('received RPC callback');
        if (!msg)
            return;
        const { content, properties } = msg;
        const { correlationId } = properties;
        const promise = this.queryMap.get(correlationId);
        if (!promise)
            return;
        const { resolve } = promise;
        this.queryMap.delete(correlationId);
        console.log('it resolved!');
        // Decode the Buffer object and pass it to the stored resolve function,
        // which will return it to the correct Apollo resolver.
        return resolve(this.decode(content));
    }
    async connect() {
        // establish connection to rabbitmq
        console.log('Opening new connection to RabbitMQ.');
        Amqp.connect(this.config)
            .then(async (conn) => {
            // save connection for later
            this.conn = conn;
            this.openChannel(conn);
        }).catch((err) => {
            console.log('error in connection: ', err);
        });
    }
    decode(msg) {
        try {
            return JSON.parse(msg.toString());
        }
        catch (err) {
            console.error(`Broker.decode was likely passed a poorly formed message: ${err}`);
            return null;
        }
    }
}
exports.Broker = Broker;
//# sourceMappingURL=broker.js.map