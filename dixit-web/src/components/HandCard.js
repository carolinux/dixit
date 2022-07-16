import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import CardMedia from '@material-ui/core/CardMedia';
import CardContent from "@material-ui/core/CardContent";
import Card from '@material-ui/core/Card';
import Typography from '@material-ui/core/Typography';
import { HowToVote } from '@material-ui/icons';
import ListItem from '@material-ui/core/ListItem';

const useStyles = makeStyles(() => ({
  card: {
    width: 150,
    height: 224,
  }
}));

export default function HandCard(props) {
  const { card, cardStatuses, gameState } = { ...props };
  const pictureUrl = `${process.env.PUBLIC_URL}/resources/pictures/cards/medusa/${card}.jpg`;
  const classes = useStyles();

  return (
    <Card raised className={ classes.cardContainer }>
      <CardMedia
        className={ classes.card }
        image={ pictureUrl } />
               {cardStatuses && cardStatuses.myPlayed  && cardStatuses.myPlayed === card && gameState === "waiting_for_votes" &&
                <CardContent>
              <Typography style={{ fontFamily: 'Lobster' }}>
               my card
              </Typography>

            </CardContent>}

                {cardStatuses && cardStatuses.myVoted  && cardStatuses.myVoted === card && gameState === "waiting_for_votes" &&
                <CardContent>
              <Typography style={{ fontFamily: 'Lobster' }}>
               my vote
              </Typography>

            </CardContent>}

            {cardStatuses && cardStatuses.summary  && cardStatuses.summary[card] && gameState === "round_revealed" &&
                <CardContent>
              <Typography>

               {cardStatuses.summary[card].isNarrator && <span style={{'color':'green', fontFamily: 'Lobster' }}>{cardStatuses.summary[card].player}</span>}
               {!cardStatuses.summary[card].isNarrator && <span style={{'color':'#CB4C4E', fontFamily: 'Lobster' }}>{cardStatuses.summary[card].player}</span>}
               {cardStatuses.summary[card].votes.length>0 &&
                cardStatuses.summary[card].votes.map((voter) => <ListItem style={{textAlign: 'left'}}><HowToVote/>{voter}</ListItem>)
               }


              </Typography>

            </CardContent>}
    </Card>
  );
}
