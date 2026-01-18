import React, {Fragment, useState} from 'react';
import axios from 'axios';
import { makeStyles } from '@material-ui/core/styles';
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
import { useDrop } from 'react-dnd';
import { ItemTypes } from './LolEmoji';

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    minWidth: '100%',
    minHeight: 224,
    width: '50%',
    justifyContent: 'left'
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
  },
   text: {
    fontFamily: 'Lobster',
    //textAlign: 'center',
    //justifySelf: 'center',
    position: 'relative',
   // bottom: 300,
    left: '50%',
  }
}));

const DroppableCard = ({ card, cardStatuses, gameState, onClick, onLolDrop, canDrop, imageFolder }) => {
  const [{ isOver, canDropHere }, drop] = useDrop(() => ({
    accept: ItemTypes.LOL_EMOJI,
    drop: () => onLolDrop(card),
    canDrop: () => canDrop,
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
      canDropHere: !!monitor.canDrop(),
    }),
  }), [card, canDrop, onLolDrop]);

  return (
    <Button
      ref={drop}
      onClick={onClick}
      style={{
        backgroundColor: isOver && canDropHere ? 'rgba(255, 215, 0, 0.3)' : 'transparent',
        border: isOver && canDropHere ? '2px dashed gold' : 'none',
      }}
    >
      <HandCard card={card} cardStatuses={cardStatuses} gameState={gameState} imageFolder={imageFolder} />
    </Button>
  );
};

export default function CardsPlayed(props) {
  const { cards, gameState, isNarrator, transitionGame, cardStatuses, castLol, imageFolder = 'medusa' } = { ...props };
   const [open, setOpen] = useState(false);
  const [cardToSelect, setCardToSelect] = useState(undefined);
  const classes = useStyles();
  const audio = new Audio(clickCardSound);
  audio.volume = 0.2;
  const audioError = new Audio(clickCardErrorSound);
  audioError.volume = 0.2;

  const openDialog = () => {
    setOpen(true);
  };

  const closeDialog = () => {
    setOpen(false);
  };

  const play = (card) => {

    if (cardStatuses && cardStatuses.myPlayed==card) {
        audioError.play();
        return;
    }


    !!card && setCardToSelect(card);
    audio.play();
    console.log('selected card '+card);
    openDialog();
  }

  const showDialog = gameState == 'waiting_for_votes' && !isNarrator;
  const question = "Sure to vote for this card?";


  const castVote = () => {
    let playedData = { vote: cardToSelect};
    closeDialog();
    transitionGame('vote', playedData);


  }
  const cancelSelection = () => {

    setCardToSelect(undefined);
    closeDialog();
  }


  return (
  <Fragment>
      <div className={classes.root}  >
        {showDialog && cards.map((card, i) =>
          <DroppableCard
            key={card+'_'+i}
            card={card}
            cardStatuses={cardStatuses}
            gameState={gameState}
            onClick={() => play(card)}
            onLolDrop={castLol}
            canDrop={cardStatuses && cardStatuses.myPlayed !== card}
            imageFolder={imageFolder}
          />)
        }

        {!showDialog && cards.map((card,i) =>
         <Button key={card+"_"+i}>
            <HandCard card={card} cardStatuses={cardStatuses} gameState={gameState} imageFolder={imageFolder} />
          </Button>)
        }

        {showDialog && <Dialog
          open={open}
          onClose={closeDialog}>

          <CardMedia
            className={classes.media}
            image={`${process.env.PUBLIC_URL}/resources/pictures/cards/${imageFolder}/${cardToSelect}.jpg`}
            />

          <Fragment>
            <Typography variant='h6' className={classes.dialog}>
              {question}
            </Typography>
          </Fragment>

          <DialogActions className={classes.controls}>
            <Button onClick={cancelSelection} color='secondary'>
              <ClearIcon />
            </Button>
            <Button onClick={castVote} color='secondary'>
              <CheckIcon style={{ fill: '#39ff14' }}/>
            </Button>
          </DialogActions>
        </Dialog>}
      </div>
    </Fragment>
  )
}
