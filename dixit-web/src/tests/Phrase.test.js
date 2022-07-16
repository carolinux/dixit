import * as React from 'react';
import { render } from '@testing-library/react';
import axios from 'axios';
import Phrase from '../components/Phrase';

// Mock axios
jest.mock('axios')

describe('Phrase', () => {

  it('renders correct phrase from data', async () => {
    const mockData = {
      data:
        { phrase: 'foo' }
      };

    axios.get.mockResolvedValue(mockData);

    const { findAllByText } = render(
      <Phrase url={'localhost:5000'} />
    );

    const text = await findAllByText(/foo/);
    expect(text).toHaveLength(1);
  });
});
