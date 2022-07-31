import React, { Fragment, useState} from 'react';
import axios from 'axios';
import { makeStyles } from '@material-ui/core/styles';
import { getTexts } from './resources/Texts';
import TextField from '@material-ui/core/TextField';
import Button from '@material-ui/core/Button';
import HandCard from './HandCard';
import Dialog from '@material-ui/core/Dialog';
import DialogContent from '@material-ui/core/DialogContent';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogActions from '@material-ui/core/DialogActions';
import Typography from '@material-ui/core/Typography';
import CardMedia from '@material-ui/core/CardMedia';
import clickCardSound from './assets/sounds/playCard.mp3'
import clickCardErrorSound from './assets/sounds/error.mp3'


const useStyles = makeStyles(() => ({
  root: {
    textAlign: 'center'
  },
  title: {
    fontFamily: 'Lobster',
    textAlign: 'center',
    color: 'white'
  },
  dialog: {
    fontFamily: 'Lobster',
    textAlign: 'center',
    paddingTop: 20,
   // height: 500,
   // width: 300
  },
  media: {
    height: 400,
    width: 300
  },
  controls: {
    justifyContent: 'center'
  }
}));


function determinePrompt(gameState, isNarrator, cardStatuses) {


    if (gameState === "waiting_for_narrator" && isNarrator) {
    return "Choose a card and an associated phrase!";
    }
    if (gameState === "waiting_for_narrator" && !isNarrator) {
    return "Waiting for narrator to choose a card and phrase.";
    }

    if (gameState === "waiting_for_players" && (isNarrator || (cardStatuses && cardStatuses.myPlayed !== ''))) {
    return "Waiting for the other players to choose their decoys.";
    }
    if (gameState === "waiting_for_players" && !isNarrator) {
    return "Choose a decoy card!";
    }

     if (gameState === "waiting_for_votes" &&  (isNarrator || (cardStatuses && cardStatuses.myVoted !== ''))) {
    return "Waiting for the other players to cast their votes.";
    }
    if (gameState === "waiting_for_votes" && !isNarrator) {
    return "Vote the card that you think matches the phrase!";
    }

    if (gameState === "round_revealed") {
    return "Results revealed!";
    }

    if (gameState === "waiting_to_start") {
    return "Waiting for the game to start..";
    }

    return gameState;




};


function shouldShowDialog(gameState, isNarrator, cardStatuses) {


 if (gameState === "waiting_for_narrator" && isNarrator) {
    return true;
 }

  if (gameState === "waiting_for_players" && !isNarrator && (!cardStatuses || (cardStatuses.myPlayed === ''))) {
    return true;
 }

 return false;
}


export default function Hand(props) {
  const {isNarrator, player, cards, transitionGame, gameState, cardStatuses } = { ...props };
  const classes = useStyles();
  const [open, setOpen] = useState(false);
  const [cardToSelect, setCardToSelect] = useState(undefined);
  const [phrase, setPhrase] = useState('');
  const [formError, setFormError] = useState(false);


  const texts = getTexts();
  const audio = new Audio(clickCardSound);
  const audioError = new Audio(clickCardErrorSound);

  const question = isNarrator ? texts.cardSelectionDialog.question.mainPlayer
    : texts.cardSelectionDialog.question.otherPlayers;

   const prompt = determinePrompt(gameState, isNarrator, cardStatuses);
   const showDialog = shouldShowDialog(gameState, isNarrator, cardStatuses);



  const openDialog = () => {
    setOpen(true);
  };

  const closeDialog = () => {
    setOpen(false);
  };

  const play = (card) => {
    !!card && setCardToSelect(card);
    audio.play();
    openDialog();
  }

  const selectCard = () => {
    let playedData = { card: cardToSelect};
    console.log('phrase: ' + phrase);
    if (isNarrator) {
      if (!!phrase) {
        setFormError(false);
        //setPhrase('');
        closeDialog();
        playedData = { ...playedData, phrase: phrase }
        transitionGame('set', playedData);
        setPhrase(''); // so as to reset for next round
      } else {
        setFormError(true);
      }

    }
    else {
       closeDialog();
       transitionGame('set', playedData);
    }

  }

  const addPhrase = (event) => {
    const value = event && event.target && event.target.value;
    setPhrase(value);
  }


  return (
    <Fragment>
      <div className={classes.root}>
        {showDialog && cards.map((card, i) =>
          <Button key={card+'_'+i} onClick={() => play(card)}>
            <HandCard card={card}/>
          </Button>)
        }

        {!showDialog && cards.map((card, i) =>
         <Button key={card+"_"+i} onClick={() => audioError.play()}>
            <HandCard card={card}/>
          </Button>)
        }

        {showDialog && <Dialog
          open={open}
          onClose={closeDialog}>

          <CardMedia
            className={classes.media}
            image={`${process.env.PUBLIC_URL}/resources/pictures/cards/medusa/${cardToSelect}.jpg`} />

          <Fragment>
            <Typography variant='h6' className={classes.dialog}>
              {question}
            </Typography>
          </Fragment>
          { isNarrator &&
            <DialogContent>
              <DialogContentText>
                <TextField onChange={addPhrase} fullWidth
                  helperText='Describe your card!'
                  error={formError}
                />
              </DialogContentText>
            </DialogContent>
          }

          <DialogActions className={classes.controls}>
            <Button onClick={closeDialog} color='secondary'>
              <ClearIcon />
            </Button>
            <Button onClick={ selectCard } color='secondary'>
              <CheckIcon style={{ fill: '#39ff14' }}/>
            </Button>
          </DialogActions>
        </Dialog>}
       <Fragment>
        <Typography variant='h6' className={classes.dialog}>
         {prompt}
        </Typography>
        </Fragment>
      </div>
    </Fragment>
  );
}
