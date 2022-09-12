import React, {useEffect, useState, Fragment} from 'react';
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';
import Grid from '@material-ui/core/Grid';
import { makeStyles } from '@material-ui/core/styles';
import { useHistory, useParams } from "react-router-dom";
import Typography from '@material-ui/core/Typography';
import axios from 'axios';
import Sound from 'react-sound'


const optionsTemplate = {
  chart: {
    type: 'column'
  },
  colors: ['#d7d7d7', '#c9b037', '#ad8a56'], // silver, gold, bronze
  title: {
    text: 'Score',
    style: {
       fontFamily: 'Lobster',
       fontSize: '40px'
    }
  },
  legend: {
    itemStyle: {
       fontFamily: 'Lobster',
       fontSize: '25px'
    }
  },
  xAxis: {
     labels: {
        enabled: false
     },
     categories: ['Medal']
  },
  yAxis: {
    min: 0,
    labels: {
      overflow: 'justify',
      style: {
       fontFamily: 'Lobster',
       fontSize: '20px'
      }
    }
  },
  series: [],
  credits: {
    enabled: false
  }
};

const useStyles = makeStyles((theme) => ({

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
}));

export default function Winners() {
  const classes = useStyles();
  const {gid} = useParams();
  const [options, setOptions] = useState(undefined);
  const [tricksters, setTricksters] = useState(undefined);
  const [soundStatus, setSoundStatus] = useState(Sound.status.STOPPED)
  const soundUrl = `${process.env.PUBLIC_URL}/resources/sounds/ending.mp3`;

  let history = useHistory();
  const axiosWithCookies = axios.create({
  withCredentials: true
  });


  const updateState = async () => {
    axiosWithCookies.get(process.env.REACT_APP_API_URL+ '/games/' + gid)
     .then(resp => {
       //console.log(resp.data.game.winners);
       let winners = resp.data.game.winners.winners
       let tricksters = resp.data.game.winners.tricksters
       //let winners = [{player: "First", score: 100}, {player: "Second", score: 80}]
       //let tricksters = {tricksters: ['anna', 'betty', 'mike'], score: 42};

       if (tricksters) {
            setTricksters(tricksters);
       }

       if (!options) {

       let newOptions = JSON.parse(JSON.stringify(optionsTemplate));
       newOptions.yAxis.min = Math.max(winners[winners.length-1].score - 5, 0);

        // rearrange the podium to be silver-gold-bronze
        let first = winners[0];
        winners[0] = winners[1];
        winners[1] = first;

       winners.map((obj)=> {newOptions.series.push({type:'column', name: obj.player, data:[obj.score]})});
       setOptions(newOptions);
       setSoundStatus(Sound.status.PLAYING);
       }

    })
    .catch(function (error) {
    console.log("error: " + JSON.stringify(error));
    history.push("/");
    })
    };

  useEffect(() => {
    updateState();
    return;
  }, []);

  const pretty_concat = (list) => {
      if (list.length < 3) { return list.join(' and '); }
      return `${list.slice(0, - 1).join(', ')}, and ${list[list.length - 1]}`;
  }

  const pretty_each = (list) => {
      if (list.length < 2) { return ''; }
      return ' each';
  }


  return (<div><HighchartsReact highcharts={Highcharts} options={options} />
    {tricksters && <Grid container spacing={2}>
      <Grid item xs={12}>
        <Grid container justifyContent='center' spacing={2}>
          <Grid item className={classes.paper}>
          <Fragment>
            <Typography className={classes.title} variant='h5'>
            Special mention:
            </Typography>
            <Typography className={classes.title} variant='h6'>
             {pretty_concat(tricksters.tricksters)} for tricking other players {tricksters.score} times{pretty_each(tricksters.tricksters)}.
            </Typography>
          </Fragment>
          </Grid>
         </Grid>
        </Grid>
       </Grid>}
      <Sound
      url={soundUrl}
      playStatus={soundStatus}
      volume={60}
    />
    </div>

  )
}
