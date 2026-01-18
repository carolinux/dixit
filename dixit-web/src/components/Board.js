import React, {useState, useEffect, useRef, Fragment} from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import CardsPlayed from './CardsPlayed';
import EventsLog from './EventsLog';
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
import Divider from '@material-ui/core/Divider';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import LolEmoji from './LolEmoji';
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
    textAlign: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
  },
  boardContainer: {
    borderRadius: 12,
    overflow: 'hidden',
    border: '3px solid #6a3805',
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
  },
  adminPanel: {
    marginTop: 24,
    padding: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
    borderRadius: 8,
    border: '1px solid rgba(0, 0, 0, 0.1)',
  },
  adminTitle: {
    fontFamily: 'Lobster',
    fontSize: '1.2rem',
    color: '#6a3805',
    marginBottom: 12,
    borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
    paddingBottom: 8,
  },
  adminSection: {
    marginBottom: 16,
  },
  adminSectionLabel: {
    fontSize: '0.75rem',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: 8,
    fontWeight: 500,
  },
  buttonGroup: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
  },
  safeButton: {
    backgroundColor: '#4caf50',
    color: 'white',
    '&:hover': {
      backgroundColor: '#388e3c',
    },
    marginRight: 8,
    marginBottom: 8,
  },
  neutralButton: {
    backgroundColor: '#1976d2',
    color: 'white',
    '&:hover': {
      backgroundColor: '#1565c0',
    },
    marginRight: 8,
    marginBottom: 8,
  },
  dangerButton: {
    backgroundColor: 'white',
    color: 'black',
    border: '1px solid #ccc',
    '&:hover': {
      backgroundColor: '#f5f5f5',
    },
    marginRight: 8,
    marginBottom: 8,
  },
  joinLink: {
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    padding: '8px 12px',
    borderRadius: 4,
    fontSize: '0.85rem',
    wordBreak: 'break-all',
    marginTop: 8,
  },
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
  audioReveal.volume = 0.2;
  audioPhrase.volume = 0.1;
  audioStart.volume = 0.2;

  const [players, setPlayers] = useState([]);
  const [updateTime, setUpdateTime] = useState(null);
  const [gameState, setGameState] = useState('');
  const [cards, setCards] = useState([]); // cards in hand
  const [playedCards, setPlayedCards] = useState([]); // cards active in round
  const [messages, setMessages] = useState([]);
  const [cardStatuses, setCardStatuses] = useState({}); //statuses of cards in round relative to player or players, depending on game state
  const [isNarrator, setIsNarrator] = useState(false);
  const [isCreator, setIsCreator] = useState(false);
  const [phrase, setPhrase] = useState('');
  const [socket, setSocket] = useState(null);
  const [lobby, setLobby] = useState([]);
  const [imageFolder, setImageFolder] = useState('medusa');

  let currTimeout = undefined;
  const messagesEndRef = useRef(null);

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
        setIsCreator(game.isCreator)
        setGameState(game.state);
        setCardStatuses(game.cardStatuses);
        setPlayers(game.playerList);
        setCards(game.roundInfo.hand);
        setPhrase(game.roundInfo.phrase);
        setLobby(game.lobby || []);
        setImageFolder(game.imageFolder || 'medusa');
        if (message) {
            let messages2 = messages;
            messages2.push(message);
            // keep only last 6 messages
            if (messages2.length > 6) {
                messages2 = messages2.slice(messages2.length-6);
            }
            setMessages(messages2);
        }
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

  const addAiPlayer = () => {
    axiosWithCookies.post(process.env.REACT_APP_API_URL + '/games/' + gid + '/add-ai', {})
      .then(resp => {
        let game = resp.data.game;
        updateFromApi(game);
      })
      .catch(function (error) {
        console.log(error);
      });
  };

  const castLol = (card) => {
    axiosWithCookies.put(process.env.REACT_APP_API_URL + '/games/' + gid + '/lol', { lol: card })
      .then(resp => {
        let game = resp.data.game;
        updateFromApi(game);
      })
      .catch(function (error) {
        console.log(error);
      });
  };

  const approveJoin = (playerName) => {
    axiosWithCookies.put(process.env.REACT_APP_API_URL + '/games/' + gid + '/approve-join/' + encodeURIComponent(playerName))
      .then(resp => {
        let game = resp.data.game;
        updateFromApi(game);
      })
      .catch(function (error) {
        console.log(error);
      });
  };

  const denyJoin = (playerName) => {
    axiosWithCookies.put(process.env.REACT_APP_API_URL + '/games/' + gid + '/deny-join/' + encodeURIComponent(playerName))
      .then(resp => {
        let game = resp.data.game;
        updateFromApi(game);
      })
      .catch(function (error) {
        console.log(error);
      });
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
    currTimeout = setTimeout(() => updateState(), 10000);
  })
  };


  useEffect(() => {

    console.log("Inside use effect: Game state="+gameState);

     const connectSocket = () => {

        if (socket === null || (socket && socket.readyState == 3)) {

        let socket2 = io(process.env.REACT_APP_API_URL);

          socket2.on('connect', function() {
            console.log("socket connected");
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
    connectSocket();
    //messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    return () => {
      if (currTimeout) {
       clearTimeout(currTimeout);
       }
    }
  }, []); // call useEffect every time the updateTime of the game changes



  return (
    <DndProvider backend={HTML5Backend}>
    <Container>
      <Grid container className={classes.boardContainer}>

         <Grid item sm={2}  className={[classes.cardsPlayed, classes.grid, classes.gridtl]}  style={{ backgroundColor: 'rgba(128,0,128, 0.2)' }}>
       <Typography variant='h3' className={classes.title}>
          BOARD >
        </Typography>
                     <Typography variant='body1'>
          Cards will appear here when played.
        </Typography>
        {gameState === 'waiting_for_votes' && !isNarrator && !cardStatuses.myLolled && (
          <div style={{ marginTop: '8px' }}>
            <LolEmoji />
          </div>
        )}
        {gameState === 'waiting_for_votes' && !isNarrator && cardStatuses.myLolled && (
          <div style={{ marginTop: '8px', fontFamily: 'Lobster' }}>
            😂 Lol given!
          </div>
        )}

             <Typography variant='h3' className={classes.title}>
             <p></p><p></p>
          HAND <KeyboardArrowDown style={{ fontSize: '42px' }}/>
        </Typography>
        <Typography variant='body1'>
         Those are your cards, not visible to other players.
        </Typography>
        </Grid>


        <Grid item sm={10} className={[classes.cardsPlayed, classes.grid, classes.gridtr]}>
           <CardsPlayed cards={playedCards} gameState={gameState} isNarrator={isNarrator} transitionGame={transitionGame} cardStatuses={cardStatuses} castLol={castLol} imageFolder={imageFolder}/>
        </Grid>

         <Grid item sm={12} className={[classes.grid, classes.gridb]}>
          <Phrase phrase={phrase}/>
        </Grid>




        <Grid item sm={10} className={[classes.grid, classes.cardsPlayed]}>
          <Hand isNarrator={isNarrator} player={mainPlayer} cards={cards} transitionGame={transitionGame} gameState={gameState} cardStatuses={cardStatuses} imageFolder={imageFolder}/>
        </Grid>

         <Grid item sm={2} className={[classes.grid, classes.gridl, classes.cardsPlayed]} style={{ backgroundColor: 'rgba(128,0,128, 0.2)' }}>
          <Players players={players}/>
          <EventsLog messages={messages} messagesEndRef={messagesEndRef}/>
        </Grid>

        {/* Next Round Button - visible to all players */}
        <Grid item sm={12}>
          {gameState==="round_revealed" && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Button size='large' onClick={() => transitionGame('next')} className={classes.safeButton}>
                {texts.stateTransitions.next}
              </Button>
            </div>
          )}
        </Grid>

        {/* Admin Panel - only visible to game creator */}
        {isCreator && (
          <Grid item sm={12}>
            <div className={classes.adminPanel}>
              <Typography className={classes.adminTitle}>
                🎮 Game Host Controls
              </Typography>

              {/* Game Setup Section - only during waiting_to_start */}
              {gameState === "waiting_to_start" && (
                <div className={classes.adminSection}>
                  <Typography className={classes.adminSectionLabel}>
                    Game Setup
                  </Typography>
                  <div className={classes.buttonGroup}>
                    <Button size='medium' onClick={() => transitionGame('start')} className={classes.safeButton}>
                      ▶ {texts.stateTransitions.start}
                    </Button>
                    <Button size='medium' onClick={() => addAiPlayer()} className={classes.neutralButton}>
                      🤖 Add AI Player
                    </Button>
                  </div>
                  <div className={classes.joinLink}>
                    <strong>Invite link:</strong> {process.env.REACT_APP_API_URL}/join/{gid}
                  </div>
                </div>
              )}

              {/* Game Management Section */}
              <div className={classes.adminSection}>
                <Typography className={classes.adminSectionLabel}>
                  Game Management
                </Typography>
                <div className={classes.buttonGroup}>
                  <Button size='medium' onClick={() => transitionGame('rematch')} className={classes.neutralButton}>
                    🔄 {texts.stateTransitions.rematch}
                  </Button>
                  <Button size='medium' variant='outlined' onClick={() => transitionGame('abandon')} className={classes.dangerButton}>
                    ⚠️ {texts.stateTransitions.abandon}
                  </Button>
                </div>
              </div>

              {/* Player Management Section */}
              {players.length > 0 && (
                <div className={classes.adminSection}>
                  <Typography className={classes.adminSectionLabel}>
                    Remove Players
                  </Typography>
                  <div className={classes.buttonGroup}>
                    {players.map((player) => (
                      <Button
                        key={player.name}
                        size='small'
                        variant='outlined'
                        onClick={() => transitionGame('remove/'+player.name)}
                        className={classes.dangerButton}
                      >
                        ✕ {player.name}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Grid>
        )}

        {/* Lobby Join Requests - only visible to creator */}
        {isCreator && lobby.length > 0 && (
          <Grid item sm={12} style={{ marginTop: 16, padding: 16, backgroundColor: 'rgba(255, 193, 7, 0.2)', borderRadius: 8 }}>
            <Typography variant='h6' style={{ fontFamily: 'Lobster', marginBottom: 8 }}>
              Players wanting to join:
            </Typography>
            {lobby.map((entry) => (
              <div key={entry.name} style={{ display: 'flex', alignItems: 'center', marginBottom: 8, gap: 8 }}>
                <Typography style={{ marginRight: 8 }}>{entry.name}</Typography>
                <Button
                  size='small'
                  variant='contained'
                  style={{ backgroundColor: '#4caf50', color: 'white' }}
                  onClick={() => approveJoin(entry.name)}
                >
                  Approve
                </Button>
                <Button
                  size='small'
                  variant='contained'
                  style={{ backgroundColor: '#f44336', color: 'white' }}
                  onClick={() => denyJoin(entry.name)}
                >
                  Deny
                </Button>
                <Typography variant='caption' style={{ color: '#666' }}>
                  (joins at next round)
                </Typography>
              </div>
            ))}
          </Grid>
        )}

      </Grid>
    </Container>
    </DndProvider>
  );
}
