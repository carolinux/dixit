import React, { Fragment} from 'react';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import ListItem from '@material-ui/core/ListItem';
import List from '@material-ui/core/List';

const useStyles = makeStyles(() => ({
  container: {
//    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 12,
    padding: '12px 8px',
  },
  title: {
    fontFamily: 'Lobster',
    paddingBottom: 10,
    color: 'black'
  },
  message: {
    border: '2px solid #dedede',
    backgroundColor: '#f1f1f1',
    borderRadius: 8,
    padding: '4px 8px',
    margin: '4px 0',
  },
  darker_message: {
    borderColor: '#ccc',
    backgroundColor: '#ddd',
    borderRadius: 8,
    padding: '4px 8px',
    margin: '4px 0',
  },
  message_box: {
    height: '250px',
    overflowY: 'scroll',
  },
  list: {
    padding: 0,
  },
}));

export default function EventsLog({ messages, messagesEndRef }) {
  const classes = useStyles();
  return (
  <div className={classes.container}>
    <Typography variant='h4' className={classes.title}>
      Events
    </Typography>
    <div className={classes.message_box}>
      <List className={classes.list}>
        {messages.map((message, i) =>
          <ListItem key={i} className={i % 2 === 0 ? classes.message : classes.darker_message}>
            {message}
          </ListItem>
        )}
      </List>
      <div ref={messagesEndRef} />
    </div>
  </div>
  );
}
