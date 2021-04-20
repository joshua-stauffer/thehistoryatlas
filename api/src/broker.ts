/*
RabbitMQ broker for the History Atlas Apollo GraphQL API.

April 16th 2021
*/

import * as Amqp from 'amqplib';
import { v4 } from 'uuid'
import { Config } from './config';
import {
  ReadModelQuery
} from './types';


// Local types
interface BrokerConfig {
  protocol: string;
  hostname: string;
  port: number;
  username: string;
  password: string;
  vhost: string;
}

export interface Message {
  type: string;
  payload: any;
}

type RPCRecipient = 'request.readmodel';
type ExchangeName = 'api';

type QueryMap = Map<string, { resolve: (value: unknown) => void, reject: (reason?: any) => void }>
type callBackFunc = (msg: Amqp.ConsumeMessage | null) => Promise<void>;

interface ExchangeDetails {
  name: string;
  type: string;
  queueName: string;
  pattern: string;
  queueOptions: Amqp.Options.AssertQueue;
  callBack: callBackFunc;
  consumeOptions?: Amqp.Options.Consume;
  publishOptions?: Amqp.Options.Publish;
  exchangeOptions?: Amqp.Options.AssertExchange;
  consumerTag?: string;
  listen: boolean;
}

export class Broker {
  private config: BrokerConfig;
  private exchanges: ExchangeDetails[];
  private conn?: Amqp.Connection;
  private channel?: Amqp.Channel;
  private queryMap: QueryMap;
  

  constructor(config: Config) {
    this.connect = this.connect.bind(this);
    this.queryReadModel = this.queryReadModel.bind(this)
    this.connect.bind(this);
    this.openChannel.bind(this);
    this.queryMap = new Map()
    const { BROKER_PASS, BROKER_USERNAME, NETWORK_HOST_NAME } = config;
    this.config = {
      protocol: 'amqp',
      hostname: NETWORK_HOST_NAME,
      port: 5672,
      username: BROKER_USERNAME,
      password: BROKER_PASS,
      vhost: '/',
    }
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
      },
      listen: true
    },
    {
      name: 'commands',
      type: 'direct',
      queueName: '',
      pattern: '',
      callBack: this.handleEmitCommand.bind(this),
      consumeOptions: {
        noAck: false,
      },
      exchangeOptions: {
        durable: true
      },
      queueOptions: {
        durable: false,
      },
      listen: false
    },
      // we can add additional exchanges here, if need be
    ]
  }

  private publishRPC(
    msg: Message,
    recipient: RPCRecipient,
    exchangeName: ExchangeName
  ): Promise<unknown> {
    if (!this.channel) throw new Error('Channel doesn\'t exist');
    const exchange = this.exchanges.find(ex => ex.name === exchangeName) as ExchangeDetails;
    const queryID = v4();
    if (!this.channel.publish(
      exchange.name,
      recipient,
      Buffer.from(JSON.stringify(msg)),
      {
        replyTo: 'amq.rabbitmq.reply-to',
        correlationId: queryID
      }
    )) throw new Error('Stream is full. Try again after receiving "drain" event.')
    return new Promise((resolve, reject) => {
      this.queryMap.set(queryID, {
        resolve: resolve, reject: reject
      })
    })
  }

  public async queryReadModel(msg: ReadModelQuery): Promise<unknown> {
    // accepts a json message and publishes it.
    return this.publishRPC(msg, 'request.readmodel', 'api');
  }

  private async handleRPCCallback(msg: Amqp.ConsumeMessage | null): Promise<void> {
    // This callback is passed to the Amqp.consume method, and will be invoked
    // whenever our application wants to query the ReadModel.
    console.log('received RPC callback')
    if (!msg) return;
    const { content, properties } = msg;
    const { correlationId } = properties;
    const promise = this.queryMap.get(correlationId);
    if (!promise) return;
    const { resolve } = promise;
    this.queryMap.delete(correlationId)
    console.log('it resolved!')
    // Decode the Buffer object and pass it to the stored resolve function,
    // which will return it to the correct Apollo resolver.
    return resolve(this.decode(content))
  }

  private async handleEmitCommand(msg: Amqp.ConsumeMessage | null): Promise<void> {
    // This callback is passed to the Amqp.consume method, and is invoked
    // whenever our application wants to listen after publishing
    // a command to the WriteModel.
    // this is currently not doing anything.
  }

  // standard amqp methods for creating and maintaining the connection

  async connect(): Promise<void> {
    // establish connection to rabbitmq

    console.log('Opening new connection to RabbitMQ.')

    Amqp.connect(this.config)
      .then(async conn => {
        // save connection for later
        this.conn = conn;
        this.openChannel(conn)
      }).catch((err) => {
        console.log('error in connection: ', err);
      })
  }

  private onConnectionClosed = () => {
    // handle the connection being closed unexpected, and try to reconnect.
    console.log('connection was closed');
  }

  private onConnectionError = (err: Amqp.Message) => {
    // handle an error on the connection.
    // error is called if the server emits 'error': an operation failed due to a failed
    // precondition, or an admin closed the channel manually.
    // this won't be called if the connection closes with an error.
    console.error(`error in connection ${err}`);

  }

  private onConnectionReturn = (msg: any) => {
    // this gets called if a message is published as mandatory and the recipient
    // can't be found. 
    console.warn(`message was returned: ${msg}`);
  }

  private onConnectionDrain = () => {
    // if a connection has returned false from .publish or .sendToQueue, it will emit
    // 'drain' after it's ready for writes again.
    console.log('drained')
  }

  private openChannel = (conn: Amqp.Connection) => {
    // open a new channel

    console.log('Opening a new primary channel.')

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
      })
  }

  private declareExchanges = (channel: Amqp.Channel) => {
    // Ensure that the exchange exists. if it does and we supply different arguments,
    // the channel will be closed.

    for (let exchConf of this.exchanges) {
      channel.assertExchange(exchConf.name, exchConf.type)
        .then(() => {
          this.createQueue(channel, exchConf);
        }).catch((err) => {
          console.log(`Caught error ${err} while declaring exchange ${exchConf.name}.`)
        })
    }
  }

  private createQueue = (channel: Amqp.Channel, exchConf: ExchangeDetails) => {
    // create a queue

    channel.assertQueue(exchConf.queueName, exchConf.queueOptions)
      .then((ok) => {
        exchConf.queueName = ok.queue;
        this.bindQueue(channel, exchConf)
      }).catch((err) => {
        console.log(`Got error ${err} while creating queue ${exchConf.queueName}`);
      })
  }

  private bindQueue = (channel: Amqp.Channel, exchConf: ExchangeDetails) => {
    // bind a queue to an exchange

    const { queueName, name, pattern } = exchConf;
    channel.bindQueue(queueName, name, pattern)
      .then(() => {
        this.startListening(channel, exchConf)
      }).catch((err) => {
        console.log(`Got error ${err} while binding queue ${queueName} to ${name}`)
      })
  }

  private startListening = (channel: Amqp.Channel, exchConf: ExchangeDetails) => {
    // start consuming on an exchange
    if (!exchConf.listen) {
      console.log('Not receiving messages on queue ', exchConf.queueName)
      return
    }

    const { queueName, callBack, consumeOptions } = exchConf;
    channel.consume(
      'amq.rabbitmq.reply-to', // setting this manually for now
      callBack,
      consumeOptions
    )
      .then((ok) => {
        exchConf.consumerTag = ok.consumerTag;
        console.log('Ready to receive messages at queue ', queueName)
      })
  }

  private decode(msg: Buffer): any {
    try {
      return JSON.parse(msg.toString())
    } catch (err) {
      console.error(`Broker.decode was likely passed a poorly formed message: ${err}`)
      return null
    }

  }

}
