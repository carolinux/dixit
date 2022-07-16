import React, {useState, useEffect} from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import CardsPlayed from './CardsPlayed';
import Hand from './Hand';
import Players from './Players';
import Phrase from './Phrase';
import axios from 'axios';
import { useHistory, useParams } from "react-router-dom";
import { getTexts } from './resources/Texts';
import Typography from '@material-ui/core/Typography';
import revealSound from './assets/sounds/reveal.mp3'
import phraseSound from './assets/sounds/phrase.mp3'
import startSound from './assets/sounds/start.mp3'
import { KeyboardArrowDown } from '@material-ui/icons';


const useStyles = makeStyles(() => ({
  cardsPlayed: {
    minHeight: 320,
  },
  title: {
    fontFamily: 'Lobster',
    paddingBottom: 10,
    color: 'black'
  },

    grid: {
    minWidth: 200,
    //fontFamily: 'Lobster',
    textAlign: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    //borderRadius: '12px',

    //borderRight: 1
  },

  gridbl : {
      borderRight: '2px solid #6a3805',

  },
  gridtl : {
      borderRight: '2px solid #6a3805',
      borderBottom: '2px solid #6a3805',

  },
   gridtr : {
      borderBottom: '2px solid #6a3805',
  },

   gridb : {
      borderBottom: '2px solid #6a3805',
  },

   gridl : {
      borderLeft: '2px solid #6a3805',
  }
}));


export default function Board(props) {

  const texts = getTexts();
  const axiosWithCookies = axios.create({
  withCredentials: true
 });
 let history = useHistory();
  const {gid} = useParams();
  const [mainPlayer, setMainPlayer] = useState('')

  const classes = useStyles();
  const audioReveal = new Audio(revealSound);
  const audioPhrase = new Audio(phraseSound);
  const audioStart = new Audio(startSound);

  const [players, setPlayers] = useState([]);
  const [gameState, setGameState] = useState('');
  const [cards, setCards] = useState([]); // cards in hand
  const [playedCards, setPlayedCards] = useState([]); // cards active in round
  const [cardStatuses, setCardStatuses] = useState({}); //statuses of cards in round relative to player or players, depending on game state
  const [isNarrator, setIsNarrator] = useState(false);
  const [phrase, setPhrase] = useState('');
  let currTimeout = undefined;



  const roundCompleted = true;
  const playerPlayed = false;

  const updateFromApi = (game) => {

         let changed = false;
        if (game.player !== mainPlayer) {
            setMainPlayer(game.player);
            changed = true;
        }

       if (game.state !== gameState) {
            if (game.state === 'game_ended') {
                history.push('/board/'+gid+'/winners');
            }
            else if (game.state === 'round_revealed') {
                audioReveal.play()

            }
            else if (game.state === 'waiting_for_players' || game.state === "waiting_for_votes") {
                audioPhrase.play()
            }
            setGameState(game.state); // this re-renders the component....
            changed = true;
        }

         if (JSON.stringify(game.cardStatuses) !== JSON.stringify(cardStatuses)) {
            setCardStatuses(game.cardStatuses);
            changed = true;
        }


       if (JSON.stringify(players) !==  JSON.stringify(game.playerList)) {
            setPlayers(game.playerList);
                        //console.log('pl');
            changed = true;
       }

       if (JSON.stringify(cards) !==  JSON.stringify(game.roundInfo.hand)) {
            setCards(game.roundInfo.hand);
                        //console.log('ha');
            changed = true;
       }

         if (JSON.stringify(playedCards) !==  JSON.stringify(game.roundInfo.playedCards)) {
            setPlayedCards(game.roundInfo.playedCards);
                        //console.log('cards');
            changed = true;
       }

        if (game.isNarrator !== isNarrator) {
                    //console.log('narr');
            setIsNarrator(game.isNarrator);
            changed = true;
        }
        if (game.roundInfo.phrase !== phrase) {
            setPhrase(game.roundInfo.phrase);
            //console.log('phrase');
            changed = true;
        }
        return changed;
  }

  const transitionGame = (transition, transitionData) => {
  console.log("Call transition game");

  if (transitionData === undefined) {
    transitionData = {};
  }

  if (transition == 'start' || transition == 'next') {

    audioStart.play();
  }

   axiosWithCookies.put(process.env.REACT_APP_API_URL+ '/games/' + gid + '/' + transition, transitionData)
     .then(resp => {
       let game = resp.data.game;
       updateFromApi(game);
     })
     .catch(function (error) {
    console.log(error);
  })
  };

  const updateState = async () => {
    axiosWithCookies.get(process.env.REACT_APP_API_URL+ '/games/' + gid)
     .then(resp => {
       console.log('call update at '+  new Date().toLocaleString());
       //console.log(resp.data.game);
       let game = resp.data.game;
       let changed = updateFromApi(game);
       //console.log("changed "+changed);
       if (!changed) {
            currTimeout = setTimeout(() => updateState(), 4000)
        }
      }
     )
    .catch(function (error) {
    console.log(error);
    if(!error.response) {
        history.push('/');
        return;
    }
    if (error.response && (error.response.status === 404 || error.response.status === 401 || error.response.status === 403)) {
        history.push('/')
        return
    }
    currTimeout = setTimeout(() => updateState(), 4000);
  })

  };


  useEffect(() => {
  //console.log('inside use effect')
    const timerID = setTimeout(() => updateState(), 50)
    return () => {
      clearTimeout(timerID);
      if (currTimeout) {
      clearTimeout(currTimeout);}
    }
  }, [gameState, players, cards, playedCards, isNarrator, phrase, cardStatuses, mainPlayer]); // call useeffect every time something changes



  return (
    <Container>
      <Grid container>

         <Grid item xs={2} sm={2}  className={[classes.cardsPlayed, classes.grid, classes.gridtl]}  style={{ backgroundColor: 'rgba(128,0,128, 0.2)' }}>
       <Typography variant='h3' className={classes.title}>
          BOARD >
        </Typography>
                     <Typography variant='body1'>
          Cards will appear here when played.
        </Typography>

             <Typography variant='h3' className={classes.title}>
             <p></p><p></p>
          HAND <KeyboardArrowDown style={{ fontSize: '42px' }}/>
        </Typography>
        <Typography variant='body1'>
         Those are your cards, not visible to other players.
        </Typography>
        </Grid>


        <Grid item xs={8} sm={10} className={[classes.cardsPlayed, classes.grid, classes.gridtr]}>
           <CardsPlayed cards={playedCards} gameState={gameState} isNarrator={isNarrator} transitionGame={transitionGame}  cardStatuses={cardStatuses}/>
        </Grid>

         <Grid item xs={12} sm={12} className={[classes.grid, classes.gridb]}>
          <Phrase phrase={phrase}/>
        </Grid>



        <Grid item xs={8} sm={10} className={[classes.grid, classes.cardsPlayed]}>
          <Hand isNarrator={isNarrator} player={mainPlayer} cards={cards} transitionGame={transitionGame} gameState={gameState} cardStatuses={cardStatuses}/>
        </Grid>

         <Grid item xs={2} sm={2} className={[classes.grid, classes.gridl, classes.cardsPlayed]} style={{ backgroundColor: 'rgba(128,0,128, 0.2)' }}>
          <Players players={players}/>
        <Typography variant='body2'>
          There are {players.length} player(s) connected.
        </Typography>
        </Grid>


        <Grid item xs={2} sm={2}>

        {gameState==="waiting_to_start" && <Button size='medium' color='primary' onClick={() => transitionGame('start')} className={classes.control}>
          {texts.stateTransitions.start}
        </Button>
        }
        {gameState==="round_revealed" && <Button size='medium' color='primary' onClick={() => transitionGame('next')} className={classes.control}>
          {texts.stateTransitions.next}
        </Button>
        }
        </Grid>
      </Grid>
    </Container>
  );
}
