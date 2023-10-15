import React, { Fragment} from 'react';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import ListItem from '@material-ui/core/ListItem';
import List from '@material-ui/core/List';

const useStyles = makeStyles(() => ({
  title: {
    fontFamily: 'Lobster',
    paddingBottom: 10,
    color: 'black'
  },
  message : {
  border: '2px solid #dedede',
  backgroundColor: '#f1f1f1',
  borderRadius: '1px',
  padding: '1px',
  margin: '1px 0',
  },
 darker_message : {
  borderColor: '#ccc',
  backgroundColor: '#ddd',
  borderRadius: '1px',
  padding: '1px',
  margin: '1px 0',
  },
  message_box : {
    height: '250px',
    overflowY: 'scroll',
  }
}));

export default function EventsLog({ messages, messagesEndRef }) {
  const classes = useStyles();
  return (
  <Fragment>
          <Typography variant='h4' className={classes.title}>
            Events
          </Typography>
        <div className={classes.message_box}>
        <List>
            {messages.map((message, i) =>

              <Fragment><ListItem class={i%2 == 0 ? classes.message: classes.darker_message}>
              {message}
              </ListItem></Fragment>
                )
            }
        </List>
       <div ref={messagesEndRef} />
       </div>
  </Fragment>
  );
}
