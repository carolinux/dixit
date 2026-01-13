import React from 'react';
import { useDrag } from 'react-dnd';
import { Box } from '@material-ui/core';

export const ItemTypes = {
  LOL_EMOJI: 'lol_emoji'
};

const LolEmoji = () => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: ItemTypes.LOL_EMOJI,
    item: { emoji: '😂' },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }));

  return (
    <Box
      ref={drag}
      style={{
        fontSize: 40,
        cursor: 'grab',
        opacity: isDragging ? 0.5 : 1,
        transition: 'opacity 0.2s',
        userSelect: 'none',
      }}
    >
      😂
    </Box>
  );
};

export default LolEmoji;
