import React from 'react';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import { getTexts } from './resources/Texts';

const useStyles = makeStyles(() => ({
  title: {
    color: 'white',
    fontFamily: 'Lobster',
    textAlign: 'center'
  },
  root: {
    padding: 200
  }
}))

export default function About() {
  const classes = useStyles();
  const texts = getTexts();

  return (
    <div className={classes.root}>
      <Typography variant='h5' className={classes.title}>
        {texts.about.title}
      </Typography>
      <Typography variant='h5' className={classes.title}>
        {texts.divider}
      </Typography>
      <Typography variant='h6' className={classes.title}>
        {texts.about.description}
      </Typography>
    </div>
  );
}
