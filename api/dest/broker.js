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
class Broker {
    constructor(conf) {
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
            channel.consume(queueName, callBack, consumeOptions)
                .then((ok) => {
                exchConf.consumerTag = ok.consumerTag;
                console.log('Ready to receive messages at queue ', queueName);
            });
        };
        this.connect = this.connect.bind(this);
        const { BROKER_PASS, BROKER_USERNAME, NETWORK_HOST_NAME } = conf;
        this.conf = {
            protocol: 'amqp',
            hostname: NETWORK_HOST_NAME,
            port: 5672,
            username: BROKER_USERNAME,
            password: BROKER_PASS,
            vhost: '/',
        };
        this.exchanges = [
            {
                name: 'api',
                type: 'topic',
                queueName: 'amq.rabbitmq',
                pattern: 'request.readmodel',
                callBack: async () => console.log('callback!'),
                consumeOptions: {
                    noAck: true
                },
                exchangeOptions: {
                    durable: false
                }
            },
            // we can add additional exchanges here, if need be
        ];
    }
    async connect() {
        // establish connection to rabbitmq
        console.log('Opening new connection to RabbitMQ.');
        Amqp.connect(this.conf)
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