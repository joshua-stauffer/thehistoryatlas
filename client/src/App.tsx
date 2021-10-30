import React from 'react';
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
import { AnnotatePage } from './pages/annotatePage';
function App() {
  const entity = useReactiveVar(currentEntity)
  return (
    <Router>
      <Background>
        <MainNav />
        <Switch>
          <Route path='/search'>
            <SearchPage />
          </Route>
          <Route path='/annotate'>
            <AnnotatePage />
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
