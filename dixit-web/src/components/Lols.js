import React, { Component } from "react";
import Draggable from "react-draggable";
import { Container, Box, Typography } from "@material-ui/core";
import SentimentVerySatisfiedIcon from "@material-ui/icons/SentimentVerySatisfied";
import SentimentSatisfiedAltIcon from "@material-ui/icons/SentimentSatisfiedAlt";
import SentimentSatisfiedIcon from "@material-ui/icons/SentimentSatisfied";

class Lols extends Component {
  render() {
    return (
      <Container sx={{ textAlign: "center", mt: 5 }}>
        <Typography variant="h5" gutterBottom>
          Drag the Emojis!
        </Typography>
        <Box display="flex" justifyContent="center" gap={4}>
          <Draggable>
            <Box sx={{ cursor: "grab" }}>
              <SentimentVerySatisfiedIcon fontSize="large" color="primary" />
            </Box>
          </Draggable>
          <Draggable>
            <Box sx={{ cursor: "grab" }}>
              <SentimentSatisfiedAltIcon fontSize="large" color="secondary" />
            </Box>
          </Draggable>
          <Draggable>
            <Box sx={{ cursor: "grab" }}>
              <SentimentSatisfiedIcon fontSize="large" color="success" />
            </Box>
          </Draggable>
        </Box>
      </Container>
    );
  }
}

export default Lols;
