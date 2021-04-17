/*
Point of entry for the GraphQL API component of the History Atlas.

April 16th, 2021
*/

const { ApolloServer } = require('apollo-server');// consider switching to apollo-server-express ?
const { Broker } = require('./broker') ;
const { typeDefs } = require('./schema') ;
const { resolvers } = require('./resolvers/resolvers') 
const { Config } = require('./config') ;



const config = new Config()
const broker = new Broker(config)
//broker.connect().then(() => console.log('Broker is ready'))

export interface Context {
  broker: typeof Broker;
}

const context: Context = {
  broker: broker
}

const server = new ApolloServer({ typeDefs, resolvers, context });

server.listen().then(({ url }) => {
  console.log(`🚀  Server ready at ${url}`);
});
