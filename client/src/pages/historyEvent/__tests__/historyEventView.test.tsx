import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { HistoryEventView } from '../historyEventView';
import { MemoryRouter, RouterProvider, createMemoryRouter } from 'react-router-dom';
import { historyEventLoader } from '../historyEventLoader';
import { bachIsBorn, bachArrivesInLuneburg, bachDedicatesMass } from '../../../data';
import { HistoryEvent } from '../../../graphql/events';
import userEvent from '@testing-library/user-event';

interface CarouselProps {
  slides: JSX.Element[];
  setFocusedIndex: (index: number) => void;
  startIndex: number;
  loadNext: () => Promise<void>;
  loadPrev: () => Promise<void>;
}

// Mock the carousel component
jest.mock('../carousel', () => ({
  __esModule: true,
  default: ({ slides, setFocusedIndex, startIndex, loadNext, loadPrev }: CarouselProps) => (
    <div data-testid="mock-carousel">
      {slides[startIndex]}
      <button onClick={() => {
        setFocusedIndex(startIndex + 1);
        loadNext();
      }}>Next Event</button>
      <button onClick={() => {
        setFocusedIndex(startIndex - 1);
        loadPrev();
      }}>Previous Event</button>
    </div>
  ),
}));

// Mock fetch for API calls
global.fetch = jest.fn();

interface MockResponse {
  events: HistoryEvent[];
  index: number;
}

const mockFetch = (events: HistoryEvent[] = [], index = 0) => {
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ events, index } as MockResponse),
  });
};

describe('HistoryEventView Integration Tests', () => {
  let router: ReturnType<typeof createMemoryRouter>;

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('eventId=f423a520-006c-40d3-837f-a802fe299742')) {
        return mockFetch([bachIsBorn, bachArrivesInLuneburg], 0);
      } else if (url.includes('eventId=7f78b709-9037-45cb-b68c-e43894be7de0')) {
        return mockFetch([bachArrivesInLuneburg, bachDedicatesMass], 0);
      } else if (url.includes('direction=next')) {
        return mockFetch([bachArrivesInLuneburg, bachDedicatesMass], 1);
      } else if (url.includes('direction=prev')) {
        return mockFetch([bachIsBorn, bachArrivesInLuneburg], 0);
      }
      return mockFetch([bachIsBorn, bachArrivesInLuneburg], 0);
    });
  });

  const renderWithRouter = (initialEntries = ['/']) => {
    router = createMemoryRouter(
      [
        {
          path: '/',
          element: <HistoryEventView />,
          loader: historyEventLoader,
        },
        {
          path: '/stories/:storyId/events/:eventId',
          element: <HistoryEventView />,
          loader: historyEventLoader,
        },
      ],
      { initialEntries }
    );
    return render(<RouterProvider router={router} />);
  };

  it('displays initial event with all key properties', async () => {
    renderWithRouter(['/stories/1/events/1']);

    // Check that all key properties are visible
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: bachIsBorn.storyTitle })).toBeInTheDocument();
    });

    // For text that might be split across elements, we can check for exact text
    const textContent = screen.getByTestId('event-text').textContent;
    expect(textContent).toBe('J. S. Bach was born in Eisenach on March 21st, 1685.');

    expect(screen.getByText(`Source: ${bachIsBorn.source.title}`)).toBeInTheDocument();
  });

  it('allows navigation between events using buttons', async () => {
    renderWithRouter(['/stories/1/events/1']);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: bachIsBorn.storyTitle })).toBeInTheDocument();
    });

    // Click next event button
    await act(async () => {
      const nextButton = screen.getByRole('button', { name: 'Next Event' });
      fireEvent.click(nextButton);
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Wait for next event to load
    await waitFor(() => {
      const textContent = screen.getByTestId('event-text').textContent;
      expect(textContent).toBe('In March of 1700, J. S. Bach and Georg Erdmann arrived in Lüneburg to study at St. Michael\'s School.');
    });

    // Click previous event button
    await act(async () => {
      const prevButton = screen.getByRole('button', { name: 'Previous Event' });
      fireEvent.click(prevButton);
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Wait for previous event to load
    await waitFor(() => {
      const textContent = screen.getByTestId('event-text').textContent;
      expect(textContent).toBe('J. S. Bach was born in Eisenach on March 21st, 1685.');
    });
  });

  it('loads more events when reaching the end of the list', async () => {
    renderWithRouter(['/stories/1/events/1']);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: bachIsBorn.storyTitle })).toBeInTheDocument();
    });

    // Click next event button multiple times
    await act(async () => {
      const nextButton = screen.getByRole('button', { name: 'Next Event' });
      fireEvent.click(nextButton);
      await new Promise(resolve => setTimeout(resolve, 0));
      fireEvent.click(nextButton);
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    await waitFor(() => {
      // Verify API call was made with correct parameters
      const calls = (global.fetch as jest.Mock).mock.calls;
      const lastCall = calls[calls.length - 1];
      expect(lastCall[0]).toContain('direction=next');
    });
  });

  it('loads more events when reaching the start of the list', async () => {
    renderWithRouter(['/stories/1/events/2']);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: bachArrivesInLuneburg.storyTitle })).toBeInTheDocument();
    });

    // Click previous event button multiple times
    await act(async () => {
      const prevButton = screen.getByRole('button', { name: 'Previous Event' });
      fireEvent.click(prevButton);
      await new Promise(resolve => setTimeout(resolve, 0));
      fireEvent.click(prevButton);
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    await waitFor(() => {
      // Verify API call was made with correct parameters
      const calls = (global.fetch as jest.Mock).mock.calls;
      const lastCall = calls[calls.length - 1];
      expect(lastCall[0]).toContain('direction=prev');
    });
  });

  it('handles tag clicks and fires API events', async () => {
    renderWithRouter(['/stories/1/events/1']);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: bachIsBorn.storyTitle })).toBeInTheDocument();
    });

    // Find and click a tag button
    const firstTag = bachIsBorn.tags[0];
    const expectedPath = `/stories/${firstTag.defaultStoryId}/events/${bachIsBorn.id}`;

    await act(async () => {
      const tagButton = screen.getByRole('button', { name: firstTag.name });
      fireEvent.click(tagButton);
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Verify navigation occurred
    await waitFor(() => {
      expect(router.state.location.pathname).toBe(expectedPath);
    });
  });
}); 