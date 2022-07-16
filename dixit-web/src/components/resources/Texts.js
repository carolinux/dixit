export const getTexts = (props) => {

  const { currentPlayer } = { ...props }

  const texts = {
    title: 'Dixit',
    cardSelectionDialog: {
      question: {
        mainPlayer: 'What is your phrase?',
        otherPlayers: 'Sure you want to play this card?'
      },
      controls: {
        select: 'All set!',
        cancel: 'I changed my mind...'
      }
    },
    yourCards: 'Your cards...',
    whoseTurn: {
      currentPlayer: `It's the turn of ${currentPlayer} to play.`,
      yourTurn: 'It\'s your turn to play!'
    },
    rules: {
      title: 'How to play Dixit',
      play: 'Play!',
      description: 'Somebody will explain to you. Enjoy the game!',
    },
    about: {
      title: 'About this app',
      description: 'Developed by carolinux and emandilara'
    },
    divider: '~',
    login: {
      title: 'Choose a name & game to enter!',
      question: 'What\'s your name?',
      ready: 'I\'m ready!',
      nameUsed: 'Someone is using already this name...',
      fullGame: 'The game is full...'
    },
    navigation: {
      scoreNow: 'Score now',
      hallOfFame: 'Hall of fame',
      rules: 'How to play',
      userInfo: 'User info',
      home: 'Game',
      about: 'About'
    },
    stateTransitions: {
      start: 'Start the first round!',
      next: 'Start the next round!'

    }
  }

  return texts
}
