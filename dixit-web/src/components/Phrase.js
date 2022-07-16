import React, { Fragment } from 'react';
import axios from 'axios';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(() => ({
  phrase: {
    fontFamily: 'Lobster',
    textAlign: 'center',
    color: 'purple',
    fontStyle: 'italic',
    backgroundColor: 'rgba(255, 255, 255, 0.6)',
  }
}));

export default function Phrase(props) {
  const { phrase } = { ...props };
  const classes = useStyles();

  return (
    <Fragment>
      { !!phrase && <Typography variant='h6' className={classes.phrase}>« { phrase } »</Typography> }
    </Fragment>
  );
}
