import React from "react";
import { useEffect } from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { useQuery, useReactiveVar } from "@apollo/client";
import { addToHistory, currentEntity } from "./hooks/history";
import { GenericError, ResourceNotFoundError } from "./pages/errorPages";
import { AddCitationPage } from "./pages/addCitation";
import { LoginPage } from "./pages/login";
import { FeedPage } from "./pages/feed";
import { useTokenManager } from "./hooks/token";

import { theme } from "./baseStyle";
import { NewFeed } from "./pages/newFeed/newFeed";
import { events } from "./data";

function App() {
  const tokenManager = useTokenManager();

  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Switch>
          <Route path="/login">
            <LoginPage tokenManager={tokenManager} />
          </Route>
          <Route path="/add-citation">
            <AddCitationPage tokenManager={tokenManager} />
          </Route>
          <Route path="/">
            <NewFeed event={events[0]} next={() => null} prev={() => null} />
          </Route>
          <Route path="*">
            <ResourceNotFoundError tokenManager={tokenManager} />
          </Route>
        </Switch>
      </Router>
    </ThemeProvider>
  );
}

export default App;
