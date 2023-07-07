import React from "react";
import ReactDOM from "react-dom";
import App from "./App";
import reportWebVitals from "./reportWebVitals";

import { ApolloClient } from "@apollo/client";
import { ApolloProvider } from "@apollo/client/react";
import { cache } from "./graphql/cache";

// this comment will trigger a rebuild

export const client = new ApolloClient({
  cache,
  uri: "http://localhost:8000",  // todo: replace with env var
  connectToDevTools: true,
});

ReactDOM.render(
  <React.StrictMode>
    <ApolloProvider client={client}>
      <App />
    </ApolloProvider>
  </React.StrictMode>,
  document.getElementById("root")
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
