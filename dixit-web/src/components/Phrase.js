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
    fontSize: '1.5rem',
    backgroundColor: 'rgba(255, 255, 255, 0.6)',
    padding: '12px 24px',
//    borderRadius: 8,
//    margin: '8px auto',
//    display: 'inline-block',
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
