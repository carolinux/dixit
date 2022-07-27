import React from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import Rules from './Rules';
import About from './About';
import Login from './Login';
import Board from './Board';
import Winners from './Winners';

function AppContainer(props) {

  return (
    <Router>
      <Switch>
        <Route path='/login/:preSelectedGid'>
          <Login/>
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
