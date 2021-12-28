import React from 'react';
import { useEffect } from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route,
} from 'react-router-dom';
import { useReactiveVar } from '@apollo/client';
import { currentEntity } from './hooks/history'
import { HomePage } from './pages/home';
import { SearchPage } from './pages/search';
import { AddCitationPage } from './pages/addCitation'
import { LoginPage } from './pages/login';
import { MainNav } from './components/mainNav';
import { Background } from './baseStyle';
import { isLoggedIn } from './hooks/user';

import DateAdapter from '@mui/lab/AdapterLuxon';
import LocalizationProvider from '@mui/lab/LocalizationProvider';

function App() {
  const entity = useReactiveVar(currentEntity)
  useEffect(() => console.log('current entity is ', entity))

  return (
    <LocalizationProvider dateAdapter={DateAdapter}>
      <Router>
          <Switch>
            <Route path='/login'>
              <LoginPage />
            </Route>
            <Route path='/search'>
              <SearchPage />
            </Route>
            <Route path='/add-citation'>
              {
                true ?? isLoggedIn() 
                  ? <AddCitationPage />
                  : <LoginPage />

              }
              
            </Route>
            <Route path='/'>
              {entity ? <HomePage /> : <SearchPage/>}
            </Route>
          </Switch>
      </Router>
    </LocalizationProvider>
  );
}

export default App;
