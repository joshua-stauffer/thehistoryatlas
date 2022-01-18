import React from 'react';
import { useEffect } from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route,
} from 'react-router-dom';
import {
  useTheme,
  createTheme,
  ThemeProvider
} from '@mui/material/styles'
import { useReactiveVar } from '@apollo/client';
import { currentEntity } from './hooks/history'
import { ResourceNotFoundError } from './pages/errorPages';
import { AddCitationPage } from './pages/addCitation'
import { LoginPage } from './pages/login';
import { FeedPage } from './pages/feed';
import { isLoggedIn } from './hooks/user';

import DateAdapter from '@mui/lab/AdapterLuxon';
import LocalizationProvider from '@mui/lab/LocalizationProvider';

function App() {
  const entity = useReactiveVar(currentEntity)
  const darkTheme = createTheme({
    palette: {
      mode: "light"
    }
  })

  return (
    <ThemeProvider theme={darkTheme}>
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
