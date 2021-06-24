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
import { MainNav } from './components/mainNav';
import { Background } from './baseStyle';
function App() {
  const entity = useReactiveVar(currentEntity)
  useEffect(() => console.log('current entity is ', entity))
  return (
    <Router>
      <Background>
        <MainNav />
        <Switch>
          <Route path='/search'>
            <SearchPage />
          </Route>
          <Route path='/'>
            {entity ? <HomePage /> : <SearchPage/>}
          </Route>
        </Switch>
      </Background>
    </Router>
  );
}

export default App;
