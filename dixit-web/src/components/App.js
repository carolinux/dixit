import React from 'react';
import axios from 'axios';
import { makeStyles } from '@material-ui/core/styles';
import AppContainer from './AppContainer';

const useStyles = makeStyles(() => ({
  root: {
    backgroundImage: `url(${'./resources/pictures/board.png'})`,
    minHeight: 750
  }
}));

function App() {
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <AppContainer/>
    </div>
  );
}

export default App;