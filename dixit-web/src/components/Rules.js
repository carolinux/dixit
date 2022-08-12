import React from 'react';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import { getTexts } from './resources/Texts';

const useStyles = makeStyles(() => ({
  title: {
    color: 'black',
    fontFamily: 'Lobster',
    textAlign: 'center'
  },
  control: {
    color: '#57e3c4',
    fontFamily: 'Lobster',
    textAlign: 'center',
    textDecoration: 'none'
  },
  root: {
    background: 'rgba(0, 0, 0, 0.3)',
    padding: 200,
    minHeight: '500px'
  }
}))

export default function Rules() {
  const classes = useStyles();
  const texts = getTexts();

  return (
    <Paper className={classes.root} elevation={3}>
      <Typography variant='h5' className={classes.title}>
        {texts.rules.title}
      </Typography>
      <Typography variant='h5' className={classes.title}>
        {texts.divider}
      </Typography>
      <br />
      <Typography variant='h6' className={classes.title}>
        {texts.rules.description}
      </Typography>
      <Typography variant='h6' className={classes.control}>
        <a href='/create'>{texts.rules.play}</a>
      </Typography>
    </Paper>
  );
}
