import React, { useState, useEffect } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import axios from 'axios';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';
import CircularProgress from '@material-ui/core/CircularProgress';
import { useHistory, useParams } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  root: {
    paddingTop: 200,
    flexGrow: 1,
  },
  title: {
    fontFamily: 'Lobster',
    paddingBottom: 10,
    color: 'black'
  },
  paper: {
    height: 350,
    width: 500,
    textAlign: 'center',
    padding: 50
  },
  status: {
    fontFamily: 'Lobster',
    fontSize: '1.2rem',
    marginTop: 20,
  },
  statusPending: {
    color: '#1976d2',
  },
  statusApproved: {
    color: '#4caf50',
  },
  statusDenied: {
    color: '#d32f2f',
  },
  spinner: {
    marginTop: 30,
  }
}));

export default function LobbyWaiting() {
  const { gid, playerName } = useParams();
  const classes = useStyles();
  const history = useHistory();
  const [status, setStatus] = useState('pending');
  const [error, setError] = useState(null);

  const axiosWithCookies = axios.create({
    withCredentials: true
  });

  useEffect(() => {
    let isMounted = true;
    let intervalId = null;

    const pollStatus = async () => {
      try {
        const response = await axios.get(
          `${process.env.REACT_APP_API_URL}/games/${gid}/lobby-status/${playerName}`
        );

        if (!isMounted) return;

        const { status: newStatus, gameState } = response.data;
        setStatus(newStatus);

        if (newStatus === 'joined') {
          // Player has been added to the game, redirect to board
          // First, we need to actually join to get the cookie
          try {
            await axiosWithCookies.post(
              `${process.env.REACT_APP_API_URL}/games`,
              { player: playerName, game: gid }
            );
            history.push(`/board/${gid}`);
          } catch (joinError) {
            // If join fails, the game state might have changed, keep polling
            console.log('Join attempt failed, continuing to poll');
          }
        } else if (newStatus === 'denied') {
          // Stop polling if denied
          if (intervalId) {
            clearInterval(intervalId);
          }
        } else if (newStatus === 'not_found') {
          setError('Your request was not found. Please try joining again.');
          if (intervalId) {
            clearInterval(intervalId);
          }
        }
      } catch (err) {
        if (!isMounted) return;
        console.error('Error polling lobby status:', err);
        setError('Error checking status. Please try again.');
      }
    };

    // Poll immediately, then every 100ms
    pollStatus();
    intervalId = setInterval(pollStatus, 100);

    return () => {
      isMounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [gid, playerName, history]);

  const getStatusMessage = () => {
    switch (status) {
      case 'pending':
        return 'Waiting for the game creator to approve your request...';
      case 'approved':
        return 'You have been approved! Waiting for the next round to start...';
      case 'denied':
        return 'Sorry, your request to join was denied.';
      case 'joined':
        return 'Joining the game...';
      default:
        return 'Checking status...';
    }
  };

  const getStatusClass = () => {
    switch (status) {
      case 'pending':
        return classes.statusPending;
      case 'approved':
        return classes.statusApproved;
      case 'denied':
        return classes.statusDenied;
      default:
        return '';
    }
  };

  return (
    <Grid container className={classes.root} spacing={2}>
      <Grid item xs={12}>
        <Grid container justifyContent='center' spacing={2}>
          <Grid item className={classes.paper}>
            <div className={classes.paper}>
              <Typography variant='h4' className={classes.title}>
                Joining Game {gid}
              </Typography>
              <Typography variant='h6' className={classes.title}>
                Player: {playerName}
              </Typography>

              {error ? (
                <Typography className={`${classes.status} ${classes.statusDenied}`}>
                  {error}
                </Typography>
              ) : (
                <>
                  <Typography className={`${classes.status} ${getStatusClass()}`}>
                    {getStatusMessage()}
                  </Typography>

                  {(status === 'pending' || status === 'approved') && (
                    <CircularProgress className={classes.spinner} />
                  )}
                </>
              )}
            </div>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
}
