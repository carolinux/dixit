import React, { Fragment } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import BottomNavigation from '@material-ui/core/BottomNavigation';
import BottomNavigationAction from '@material-ui/core/BottomNavigationAction';
import PersonIcon from '@material-ui/icons/Person';
import EqualizerIcon from '@material-ui/icons/Equalizer';
import AccountBalanceIcon from '@material-ui/icons/AccountBalance';
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';
import Score from './Score';

const useStyles = makeStyles((theme) => ({
  modal: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  paper: {
    backgroundColor: theme.palette.background.paper,
    border: '2px solid #000',
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 4, 3),
  }
}));

export default function FooterNavigation() {
  const [value, setValue] = React.useState('recents');
  const [open, setOpen] = React.useState(false);

  const handleChange = (newValue) => {
    setValue(newValue);
  };

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const classes = useStyles();
  return (
    <Fragment>
      <BottomNavigation value={value} onChange={handleChange}>
        <BottomNavigationAction label='User' value='user' icon={<PersonIcon />} />
        <BottomNavigationAction label='Score' value='score' onClick={handleOpen} icon={<EqualizerIcon />} />
        <BottomNavigationAction label='Hall of fame' value='globalScore' icon={<AccountBalanceIcon />} />
      </BottomNavigation>

      <Modal
        aria-labelledby='transition-modal-title'
        aria-describedby='transition-modal-description'
        className={classes.modal}
        open={open}
        onClose={handleClose}
        closeAfterTransition
        BackdropComponent={Backdrop}
        BackdropProps={{
          timeout: 500,
        }}
      >
        <Fade in={open}>
          <div className={classes.paper}>
            <Score />
          </div>
        </Fade>
      </Modal>
    </Fragment>
  );
}
