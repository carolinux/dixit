import React, {useEffect, useState} from 'react';
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';
import { useHistory, useParams } from "react-router-dom";
import axios from 'axios';
import Sound from 'react-sound'


const optionsTemplate = {
  chart: {
    type: 'column'
  },
  colors: ['#d7d7d7', '#c9b037', '#ad8a56'], // silver, gold, bronze
  title: {
    text: 'Score of this game'
  },
  yAxis: {
    min: 0,
    title: {
      text: 'Score'
    },
    labels: {
      overflow: 'justify'
    }
  },
  series: [],
  credits: {
    enabled: false
  }
};

export default function Winners() {

  const {gid} = useParams();
  const [options, setOptions] = useState(undefined);
  const [soundStatus, setSoundStatus] = useState(Sound.status.STOPPED)
  const soundUrl = `${process.env.PUBLIC_URL}/resources/sounds/ending.mp3`;

  let history = useHistory();
  const axiosWithCookies = axios.create({
  withCredentials: true
  });


  const updateState = async () => {
    axiosWithCookies.get(process.env.REACT_APP_API_URL+ '/games/' + gid)
     .then(resp => {
       console.log('call update at '+  new Date().toLocaleString());
       console.log(resp.data.game.winners);
       let game = resp.data.game;

       if (!options) {

       let newOptions = JSON.parse(JSON.stringify(optionsTemplate));

        // rearrange the podium to be silver-gold-bronze
        let first = game.winners[0];
        game.winners[0] = game.winners[1];
        game.winners[1] = first;

       game.winners.map((obj)=> {newOptions.series.push({type:'column', name: obj.player, data:[obj.score]})});
       setOptions(newOptions);
       setSoundStatus(Sound.status.PLAYING);
       }

    })
    .catch(function (error) {
    console.log(JSON.stringify(error));
    history.push("/");
    })
    };

  useEffect(() => {
    console.log('inside use effect');
    updateState();
    return;
  }, []); // call useeffect every time something changes


  return (<div><HighchartsReact highcharts={Highcharts} options={options} />
      <Sound
      url={soundUrl}
      playStatus={soundStatus}
    />
    </div>

  )
}
