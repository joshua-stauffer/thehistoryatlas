/*
RabbitMQ broker for the History Atlas Read Side.

April 14th 2021
*/

import * as Amqp from 'amqplib';
import { v4 } from 'uuid'
import { Config } from './config';
import { APIHandler, EventHandler } from './readModel';

interface BrokerConfig {
  protocol: string;
  hostname: string;
  port: number;
  username: string;
  password: string;
  vhost: string;
  isDBInitialized: boolean;
}

type callBackFunc = (msg: Amqp.ConsumeMessage | null) => Promise<void>;

interface ExchangeDetails {
  name: string;
  type: string;
  queueName: string;
  pattern: string;
  queueOptions?: Amqp.Options.AssertQueue;
  callBack: callBackFunc;
  consumeOptions?: Amqp.Options.Consume;
  publishOptions?: Amqp.Options.Publish;
  exchangeOptions?: Amqp.Options.AssertExchange;
  consumerTag?: string;
}

export class Broker {

  private conf: BrokerConfig;
  private exchanges: ExchangeDetails[];
  private conn?: Amqp.Connection;
  private channel?: Amqp.Channel;
  private apiHandler: APIHandler;
  private eventHandler: EventHandler;

  private tmpChannel?: Amqp.Channel;
  private tmpConsumerTag?: string;
  private tmpCorrId?: string;


  constructor(conf: Config, apiCallBack: APIHandler, eventCallBack: EventHandler, isDBInitialized: boolean) {

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
    }
    this.exchanges = [
      {
        name: 'api',
        type: 'topic',
        queueName: '',
        pattern: 'request.readmodel',
        callBack: this.handleAPICallBack.bind(this),      // callbacks must be bound
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
        callBack: this.handleEventCallBack.bind(this)     // callbacks must be bound
      }
    ]
  }

  async handleAPICallBack(msg: Amqp.ConsumeMessage | null): Promise<void> {
    // passes incoming API read requests off to main application, then
    // acks or nacks the message on completion.
    if (!msg) {
      console.warn('Broker is closing the connection')
      return // add some sort of a restart logic here?
    }

    this.apiHandler(msg.content)
      .then((res) => {

        // double check that the channel is there
        if (!this.channel) {
          console.error('Channel was non-existent in handleAPICallBack')
          return
        }
        console.log('sending ', res)
        // send response
        this.channel.sendToQueue(
          msg.properties.replyTo,                         // queue we're sending to
          Buffer.from(res.toString()),                    // response from database
          {
            correlationId: msg.properties.correlationId   // id so the API knows which question this answers
          }
        )
        
      }) // not catching errors here


  }

  async handleEventCallBack(msg: Amqp.ConsumeMessage | null): Promise<void>   {
    // passes incoming Event read requests off to main application, then
    // responds with the requested data. No acknowledgements neccessary.

    if (!msg) {
      console.warn('Broker is closing the connection')
      return // add some sort of a restart logic here?
    }

    this.eventHandler(msg.content)
      .then((res) => {

        // double check that the channel is there
        if (!this.channel) {
          console.error('Channel was non-existent in handleEventCallBack')
          return
        }

        if (res) {
          // ack
          this.channel.ack(msg)
        } else {
          // nack
          this.channel.nack(msg)
        }
      })

    
  }

  async connect(): Promise<void> {
    // establish connection to rabbitmq


    Amqp.connect(this.conf)
      .then(async conn => {

        // save connection for later
        this.conn = conn;

        // do we need to initialize the database?
        if (!this.conf.isDBInitialized) {
          // block the thread until db is ready
          await this.callPlayHistory(conn)
          return
        }

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

    const { queueName, callBack, consumeOptions } = exchConf;
    channel.consume(queueName, callBack, consumeOptions)
      .then((ok) => {
        exchConf.consumerTag = ok.consumerTag;
      })
  }

  private async callPlayHistory(conn: Amqp.Connection): Promise<void> {
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

    const tmpChannel = await conn.createChannel()
    this.tmpChannel = tmpChannel;

    // set channel event listeners
    tmpChannel.on('close', () => console.error('Channel closed while replaying event stream.'));
    tmpChannel.on('error', (err) => console.error(`Channel encountered error while replaying event stream: ${err}.`));
    tmpChannel.on('return', () => console.log('Connection is back in replay event stream.'));
    tmpChannel.on('drain', () => console.log('Connection must drain in replaying event stream.'));
    
    // make sure exchange exists
    const exchangeName = 'history'
    await tmpChannel.assertExchange(exchangeName, 'direct')

    // create a temporary queue
    const { queue } = await tmpChannel.assertQueue('', {
      autoDelete: true,
      durable: true,    // durable from the point of view of the broker
      exclusive: true
    })

    // bind the queue to our history exchange
    await tmpChannel.bindQueue(queue, exchangeName, '')

    // create a message, an id, and send it to the History player
    const msg = Buffer.from(JSON.stringify(
      { replay_history: 'start', start_from: 0 }
      ))
    const corrId = v4();
    this.tmpCorrId = corrId;

    tmpChannel.publish(exchangeName, '', msg, { replyTo: queue, correlationId: corrId })

    // listen for incoming events until receiving a stop message
    const { consumerTag } = await tmpChannel.consume(queue, this.historyStreamConsumer)
    this.tmpConsumerTag = consumerTag;
  }

  async historyStreamConsumer(msg: Amqp.ConsumeMessage | null): Promise<void> {
    // callback  function for handling incoming events

    // we need these to be set to continue
    if (!this.tmpChannel) throw new Error('Temporary channel is undefined')
    if (!this.tmpConsumerTag) throw new Error('Temporary consumer tag is undefined')

    if (!msg) {
      // consumer was cancelled
      // will this happen if the broker crashes while replaying?
      console.log('History stream was closed.')
      this.tmpChannel.cancel(this.tmpConsumerTag)
      await this.tmpChannel.close();
      this.conf.isDBInitialized = true;
      return
    }
    
    if (msg.properties.correlationId !== this.tmpCorrId) {
      console.log('Received an unrelated message from the History stream.')
      return
    }

    const { content } = msg;
    const message = JSON.parse(msg.toString())

    if (message?.payload === 'end') {
      // stream is over, close this channel and restart standard listening
      this.tmpChannel.ack(msg)
      this.tmpChannel.cancel(this.tmpConsumerTag)
      await this.tmpChannel.close()
      this.conf.isDBInitialized = true;
      if (!this.conn) throw new Error('Connection is missing in History stream consumer')
      return this.openChannel(this.conn)

    } else {
      // send this message to application for processing
      if (await this.eventHandler(content)) {
        this.tmpChannel.ack(msg)
      } else {
        this.tmpChannel.nack(msg)
      }
      
    }
    
  }

}
