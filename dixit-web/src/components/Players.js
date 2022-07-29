import React, { Fragment } from 'react';
import axios from 'axios';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import SportsEsportsOutlinedIcon from '@material-ui/icons/SportsEsportsOutlined';
import { ArrowBack, ArrowForward } from '@material-ui/icons';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';


const useStyles = makeStyles(() => ({
  players: {
    color: 'black',
    backgroundColor: 'white'
    //fontFamily: 'Lobster'
  },
  narrator: {
    color: 'black',
    backgroundColor: '#c5e1a5'
    //fontFamily: 'Lobster'
  },
  title: {
    fontFamily: 'Lobster',
    textAlign: 'center',
    color: 'black'
  },
}));

export default function Players(props) {
  const { players } = { ...props };
  const classes = useStyles();
  //console.log('players: '+players);
  // className={player.isNarrator?  classes.narrator: classes.players}

  return (
  <Fragment>
  <Typography variant='h4' className={classes.title}>
  Players
  </Typography>
  <List>
    { players.map(player =>
    <Fragment><ListItem className={player.isNarrator?classes.narrator:classes.players} key={player.name}>
      <ListItemIcon  className={player.isNarrator?classes.narrator:classes.players} ><SportsEsportsOutlinedIcon  style={{ fill: 'green' }}/></ListItemIcon>
      {player.name}: {player.score} {player.roundScore>0 && <span>(+{player.roundScore})</span> }
       {player.isNarrator && <ArrowBack style={{ fill: 'green' }}/>}
    </ListItem></Fragment> )}
  </List>
  </Fragment>
  );
}
