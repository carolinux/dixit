import React, { useState } from "react";
import { DndProvider, useDrag, useDrop } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { Box, Card, Typography } from "@material-ui/core";

const ItemTypes = { EMOJI: "emoji" };

const emojis = ["😀", "🎉", "🚀", "❤️"];

const Emoji = ({ emoji, index, moveEmoji }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: ItemTypes.EMOJI,
    item: { emoji, index },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }));

  return (
    <Box
      ref={drag}
      sx={{
        fontSize: 40,
        cursor: "grab",
        opacity: isDragging ? 0.5 : 1,
        transition: "opacity 0.2s",
      }}
    >
      {emoji}
    </Box>
  );
};


const EmojiDropCard = ({ onDrop, storedEmojis }) => {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: ItemTypes.EMOJI,
    drop: (item) => onDrop(item.emoji, item.index),
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
    }),
  }));

  return (
    <Card
      ref={drop}
      sx={{
        width: 150,
        height: 150,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: isOver ? "#d0f0d0" : "white",
        border: "2px solid #ccc",
      }}
    >
      <Typography variant="h6">Card</Typography>
      {storedEmojis.map((e, i) => (
        <Typography key={i} sx={{ fontSize: 40 }}>{e}</Typography>
      ))}
    </Card>
  );
};

const Lols = () => {
  const [emojiPositions, setEmojiPositions] = useState(
    emojis.map((emoji) => ({ emoji, card: null }))
  );
  const [cards, setCards] = useState([[], []]);

const handleDrop = (emoji, emojiIndex, cardIndex) => {
  if (cardIndex !== null) {
    setEmojiPositions((prev) =>
      prev.map((e, i) => (i === emojiIndex ? { ...e, card: cardIndex } : e))
    );
    setCards((prev) => {
      const newCards = [...prev];
      newCards[cardIndex] = [...newCards[cardIndex], emoji];
      return newCards;
    });
  } else {
  console.log("dropped somewhere else")
  }
};
  return (
    <DndProvider backend={HTML5Backend}>
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
        <Box sx={{ display: "flex", gap: 2 }}>
          {emojiPositions.map((e, i) =>
            e.card === null ? (
              <Emoji key={i} emoji={e.emoji} index={i} moveEmoji={handleDrop} />
            ) : null
          )}
        </Box>

        <Box sx={{ display: "flex", gap: 2 }}>
          {cards.map((storedEmojis, index) => (
            <EmojiDropCard
              key={index}
              onDrop={(emoji, emojiIndex) => handleDrop(emoji, emojiIndex, index)}
              storedEmojis={storedEmojis}
            />
          ))}
        </Box>
      </Box>
    </DndProvider>
  );
};

export default Lols;
