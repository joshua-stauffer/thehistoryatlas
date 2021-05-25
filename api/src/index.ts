/*
Point of entry for the GraphQL API component of the History Atlas.

April 16th, 2021
*/

const { ApolloServer } = require('apollo-server');// consider switching to apollo-server-express ?
const { Broker } = require('./broker') ;
const { typeDefs } = require('./schema') ;
const { resolvers } = require('./resolvers') 
const { Config } = require('./config') ;
import { GeoServiceQuery, NLPServiceQuery, ReadModelQuery, WriteModelCommand } from './types';


const config = new Config()
const broker = new Broker(config)
broker.connect().then(() => console.log('Broker is ready'))

export interface Context {
  queryReadModel: (query: ReadModelQuery) => Promise<unknown>;
  emitCommand: (command: WriteModelCommand) => Promise<unknown>;
  queryNLP: (query: NLPServiceQuery) => Promise<unknown>;
  queryGeo: (query: GeoServiceQuery) => Promise<unknown>;
}

const context: Context = {
  queryReadModel: broker.queryReadModel,
  emitCommand: broker.emitCommand,
  queryNLP: broker.queryNLP,
  queryGeo: broker.queryGeo
}

const server = new ApolloServer({ typeDefs, resolvers, context });
server.listen().then(({ url }: any) => {
  console.log(`🚀  Server ready at ${url}`);
});
