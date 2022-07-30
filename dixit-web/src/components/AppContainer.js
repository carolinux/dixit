import React from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import Rules from './Rules';
import About from './About';
import Login from './Login';
import Join from './Join';
import Board from './Board';
import Winners from './Winners';

function AppContainer(props) {

  return (
    <Router>
      <Switch>
        <Route path='/create'>
          <Login/>
        </Route>
        <Route path='/join/:preSelectedGid'>
          <Join/>
        </Route>
        <Route path='/board/:gid/winners'>
          <Winners/>
        </Route>
        <Route path='/board/:gid'>
          <Board/>
        </Route>
        <Route path='/'>
          <Rules />
        </Route>
      </Switch>
    </Router>
  );
}

export default AppContainer;
