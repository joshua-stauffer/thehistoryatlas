"use strict";
/*
RabbitMQ broker for the History Atlas Read Side.

April 14th 2021
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
    constructor(conf, apiCallBack, eventCallBack, isDBInitialized) {
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
        this.callPlayHistory = this.callPlayHistory.bind(this);
        this.apiHandler = apiCallBack;
        this.eventHandler = eventCallBack;
        const { BROKER_PASS, BROKER_USERNAME, NETWORK_HOST_NAME } = conf;
        this.conf = {
            protocol: 'amqp',
            hostname: NETWORK_HOST_NAME,
            port: 5672,
            username: BROKER_USERNAME,
            password: BROKER_PASS,
            vhost: '/',
            isDBInitialized: isDBInitialized
        };
        this.exchanges = [
            {
                name: 'api',
                type: 'topic',
                queueName: '',
                pattern: 'request.readmodel',
                callBack: this.handleAPICallBack.bind(this),
                consumeOptions: {
                    noAck: true
                },
                exchangeOptions: {
                    durable: false
                }
            },
            {
                name: 'persisted_events',
                type: 'direct',
                queueName: 'readModel-eventlistener',
                pattern: '',
                callBack: this.handleEventCallBack.bind(this) // callbacks must be bound
            }
        ];
    }
    async handleAPICallBack(msg) {
        // passes incoming API read requests off to main application, then
        // responds with the requested data. No acknowledgements neccessary.
        if (!msg) {
            console.warn('Broker is closing the connection');
            return; // add some sort of a restart logic here?
        }
        if (!this.channel) {
            console.error('Broker.handleAPICallBack: channel is nonexistent');
            return;
        }
        const { content } = msg;
        const body = this.decode(content);
        if (!body) {
            console.warn('Broker.handleAPICallBack: discarding poorly formed message');
            return;
        }
        this.apiHandler(body)
            .then((res) => {
            // double check that the channel is there
            if (!this.channel) {
                console.error('Channel was non-existent in handleAPICallBack');
                return;
            }
            console.log('sending ', res);
            // send response
            this.channel.sendToQueue(// does this work with the direct RPC pattern? https://www.rabbitmq.com/direct-reply-to.html
            // yes, as per http://www.squaremobius.net/amqp.node/channel_api.html#connect
            msg.properties.replyTo, // queue we're sending to
            Buffer.from(JSON.stringify(res)), // response from database
            {
                correlationId: msg.properties.correlationId // id so the API knows which question this answers
            });
        }); // not catching errors here
    }
    async handleEventCallBack(msg) {
        // passes incoming Event read requests off to main application, then
        // acks or nacks the message on completion. 
        if (!msg) {
            console.warn('Broker is closing the connection');
            return; // add some sort of a restart logic here?
        }
        // double check that the channel is there
        if (!this.channel) {
            console.error('Broker.handleEventCallBack: channel is nonexistent');
            return;
        }
        const { content } = msg;
        const body = this.decode(content);
        if (!body) {
            console.warn('Broker.handleEventCallBack: discarding poorly formed message');
            this.channel.ack(msg);
            return;
        }
        this.eventHandler(body)
            .then((res) => {
            // double check that the channel is there
            if (!this.channel) {
                console.error('Broker.handleEventCallBack: channel is nonexistent');
                return;
            }
            if (res) {
                // ack
                this.channel.ack(msg);
            }
            else {
                // nack
                this.channel.nack(msg);
            }
        });
    }
    async connect() {
        // establish connection to rabbitmq
        console.log('Opening new connection to RabbitMQ.');
        Amqp.connect(this.conf)
            .then(async (conn) => {
            // save connection for later
            this.conn = conn;
            // do we need to initialize the database?
            if (!this.conf.isDBInitialized) {
                // block the thread until db is ready
                await this.callPlayHistory(conn);
                return;
            }
            this.openChannel(conn);
        }).catch((err) => {
            console.log('error in connection: ', err);
        });
    }
    async callPlayHistory(conn) {
        /*
        Creates a replay request to the History component, then listens until
        replay is complete. This method should be awaited directly, since it is
        responsible for populating the database with initial values -- no queries
        should be accepted until this call is complete. The History component
        should not close the connection until it's sure that the most up to date
        representation of it's state has been transferred -- i.e. if new events
        come in while it is replaying, it should perform an additional check at the
        end of its replay and send the additional events through before closing.
        */
        console.log('Requesting a history play back.');
        const tmpChannel = await conn.createChannel();
        this.tmpChannel = tmpChannel;
        // set channel event listeners
        tmpChannel.on('close', () => console.error('Channel closed while replaying event stream.'));
        tmpChannel.on('error', (err) => console.error(`Channel encountered error while replaying event stream: ${err}.`));
        tmpChannel.on('return', () => console.log('Connection is back in replay event stream.'));
        tmpChannel.on('drain', () => console.log('Connection must drain in replaying event stream.'));
        // make sure exchange exists
        const exchangeName = 'history';
        await tmpChannel.assertExchange(exchangeName, 'direct');
        // create a temporary queue
        const { queue } = await tmpChannel.assertQueue('', {
            autoDelete: true,
            durable: true,
            exclusive: true
        });
        // bind the queue to our history exchange
        await tmpChannel.bindQueue(queue, exchangeName, '');
        // create a message, an id, and send it to the History player
        const msg = Buffer.from(JSON.stringify({ replay_history: 'start', start_from: 0 }));
        const corrId = uuid_1.v4();
        this.tmpCorrId = corrId;
        tmpChannel.publish(exchangeName, '', msg, { replyTo: queue, correlationId: corrId });
        // listen for incoming events until receiving a stop message
        const { consumerTag } = await tmpChannel.consume(queue, this.historyStreamConsumer);
        this.tmpConsumerTag = consumerTag;
    }
    async historyStreamConsumer(msg) {
        // callback  function for handling incoming events
        // we need these to be set to continue
        if (!this.tmpChannel)
            throw new Error('Temporary channel is undefined');
        if (!this.tmpConsumerTag)
            throw new Error('Temporary consumer tag is undefined');
        if (!msg) {
            // consumer was cancelled
            // will this happen if the broker crashes while replaying?
            console.log('History stream was closed.');
            this.tmpChannel.cancel(this.tmpConsumerTag);
            await this.tmpChannel.close();
            this.conf.isDBInitialized = true;
            return;
        }
        if (msg.properties.correlationId !== this.tmpCorrId) {
            console.log('Broker.historyStreamConsumer received an offtopic message.');
            this.tmpChannel.ack(msg);
            return;
        }
        const { content } = msg;
        const body = this.decode(content);
        if (!body) {
            console.warn('Broker.historyStreamConsumer discarding poorly formed message');
            this.tmpChannel.ack(msg);
            return;
        }
        if (body?.payload === 'end') {
            // stream is over, close this channel and restart standard listening
            this.tmpChannel.ack(msg);
            this.tmpChannel.cancel(this.tmpConsumerTag);
            await this.tmpChannel.close();
            this.conf.isDBInitialized = true;
            if (!this.conn)
                throw new Error('Connection is missing in History stream consumer');
            return this.openChannel(this.conn);
        }
        else {
            // send this message to application for processing
            if (await this.eventHandler(body)) {
                this.tmpChannel.ack(msg);
            }
            else {
                this.tmpChannel.nack(msg);
            }
        }
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