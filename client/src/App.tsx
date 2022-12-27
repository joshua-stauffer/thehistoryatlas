import React from 'react';
import { useEffect } from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route,
} from 'react-router-dom';
import {
  ThemeProvider,
} from '@mui/material/styles'
import { useReactiveVar } from '@apollo/client';
import { currentEntity } from './hooks/history'
import { ResourceNotFoundError } from './pages/errorPages';
import { AddCitationPage } from './pages/addCitation'
import { LoginPage } from './pages/login';
import { FeedPage } from './pages/feed';
import { isLoggedIn } from './hooks/user';


import { theme } from './baseStyle';

function App() {
  const entity = useReactiveVar(currentEntity)
  

  return (
    <ThemeProvider theme={theme}>
      <Router>
          <Switch>
            <Route path='/login'>
              <LoginPage />
            </Route>
            <Route 
              path='/add-citation'
            >
              {
                true ?? isLoggedIn() 
                  ? <AddCitationPage />
                  : <LoginPage />

              }
            </Route>
            <Route path='/'>
              <FeedPage />
            </Route>
            <Route path='*'>
              <ResourceNotFoundError />
            </Route>  
          </Switch>
      </Router>
    </ThemeProvider>
  );
}

export default App;
