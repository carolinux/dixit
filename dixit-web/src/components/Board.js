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
import io from 'socket.io-client';


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
  const [updateTime, setUpdateTime] = useState(null);
  const [gameState, setGameState] = useState('');
  const [cards, setCards] = useState([]); // cards in hand
  const [playedCards, setPlayedCards] = useState([]); // cards active in round
  const [messages, setMessages] = useState([]);
  const [cardStatuses, setCardStatuses] = useState({}); //statuses of cards in round relative to player or players, depending on game state
  const [isNarrator, setIsNarrator] = useState(false);
  const [phrase, setPhrase] = useState('');
  const [socket, setSocket] = useState(null);




  let currTimeout = undefined;

  const roundCompleted = true;
  const playerPlayed = false;

  const updateFromApi = (game, message) => {
        setMainPlayer(game.player);
        setIsNarrator(game.isNarrator);
        setPlayedCards(game.roundInfo.playedCards);
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
        }
        setGameState(game.state);
        setCardStatuses(game.cardStatuses);
        setPlayers(game.playerList);
        setCards(game.roundInfo.hand);
        setPhrase(game.roundInfo.phrase);
        let messages2 = messages;
        messages2.push(message);
        console.log("Updated messages: "+messages2);
        setMessages(messages2);
        setUpdateTime(Date.now());
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

  const updateState = async (message) => {
    axiosWithCookies.get(process.env.REACT_APP_API_URL+ '/games/' + gid)
     .then(resp => {
       console.log('call update at '+  new Date().toLocaleString());
       //console.log(resp.data.game);
       let game = resp.data.game;
       let changed = updateFromApi(game, message);
       //console.log("changed "+changed);
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
    currTimeout = setTimeout(() => updateState(), 1000);
  })
  };


  useEffect(() => {

    console.log("Inside use effect: Game state="+gameState);

     const connectSocket = () => {

        if (socket === null || (socket && socket.readyState == 3)) {

        let socket2 = io(process.env.REACT_APP_API_URL);

          socket2.on('connect', function() {
            console.log("socket connected");
            //setIsConnected(true);
            socket2.emit('join', {room: gid});
        });

        socket2.on('disconnect', function() {
            console.error("socket disconnected, will attempt to reconnect in one second");
            setTimeout(function() {
              connectSocket();
            }, 1000);
        });

         socket2.on("error", (err) => {
            console.error('Socket encountered error: ', err.message, 'Closing socket');
            socket2.close();
        });

        socket2.on("update", (data) => {
            const packet = JSON.parse(data);
            console.log("received game update: "+JSON.stringify(packet));
            updateState(packet['data']);

        });
        setSocket(socket2);
        }

     };

    console.log("Messages2 "+messages);
    connectSocket();
    return () => {
      if (currTimeout) {
       clearTimeout(currTimeout);
       }
    }
  }, [updateTime]); // call useeffect every time something changes



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


        <Grid item xs={2} sm={2}>
            <div>
            {messages.map(message =>  <li key={message}>  {message} </li>)}
            </div>
        </Grid>



      </Grid>
    </Container>
  );
}
