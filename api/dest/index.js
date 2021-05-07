"use strict";
/*
Point of entry for the GraphQL API component of the History Atlas.

April 16th, 2021
*/
Object.defineProperty(exports, "__esModule", { value: true });
const { ApolloServer } = require('apollo-server'); // consider switching to apollo-server-express ?
const { Broker } = require('./broker');
const { typeDefs } = require('./schema');
const { resolvers } = require('./resolvers');
const { Config } = require('./config');
const config = new Config();
const broker = new Broker(config);
broker.connect().then(() => console.log('Broker is ready'));
const context = {
    queryReadModel: broker.queryReadModel,
    emitCommand: broker.emitCommand
};
const server = new ApolloServer({ typeDefs, resolvers, context });
server.listen().then(({ url }) => {
    console.log(`🚀  Server ready at ${url}`);
});
//# sourceMappingURL=index.js.map