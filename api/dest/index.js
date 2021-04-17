"use strict";
const { ApolloServer } = require('apollo-server'); // consider switching to apollo-server-express ?
const { Broker } = require('./broker');
const { typeDefs } = require('./schema');
const { resolvers } = require('./resolvers/resolvers');
const { Config } = require('./config');
const config = new Config();
//const broker = new Broker(config)
//broker.connect().then(() => console.log('Broker is ready'))
const server = new ApolloServer({ typeDefs, resolvers });
server.listen().then(({ url }) => {
    console.log(`🚀  Server ready at ${url}`);
});
//# sourceMappingURL=index.js.map