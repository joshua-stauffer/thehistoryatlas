import React from "react";
import { useEffect } from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { useQuery, useReactiveVar } from "@apollo/client";
import { addToHistory, currentEntity } from "./hooks/history";
import { ResourceNotFoundError } from "./pages/errorPages";
import { AddCitationPage } from "./pages/addCitation";
import { LoginPage } from "./pages/login";
import { FeedPage } from "./pages/feed";
import { useTokenManager } from "./hooks/token";

import { theme } from "./baseStyle";
import {
  DefaultEntityResult,
  DefaultEntityVars,
  DEFAULT_ENTITY,
} from "./graphql/defaultEntity";

function App() {
  const entity = useReactiveVar(currentEntity);
  const tokenManager = useTokenManager();

  const {
    loading: defaultEntityLoading,
    error: defaultEntityError,
    data: defaultEntityData,
  } = useQuery<DefaultEntityResult, DefaultEntityVars>(DEFAULT_ENTITY);

  useEffect(() => {
    if (!!defaultEntityData) {
      addToHistory({
        entity: {
          guid: defaultEntityData.defaultEntity.id,
          type: defaultEntityData.defaultEntity.type,
          name: defaultEntityData.defaultEntity.name,
        },
        lastSummaryGUID: undefined,
      });
    }
  }, [defaultEntityData]);

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
            {entity === null ? (
              <h1>Loading Feed</h1>
            ) : (
              <FeedPage tokenManager={tokenManager} />
            )}
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
