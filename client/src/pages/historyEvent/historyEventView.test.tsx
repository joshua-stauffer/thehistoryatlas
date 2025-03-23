import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import { HistoryEventView } from './historyEventView';
import { MemoryRouter } from 'react-router-dom';
import { useMediaQuery } from '@mui/material';
import { useLoaderData, useNavigate } from 'react-router-dom';

// Mock all required hooks and components
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLoaderData: jest.fn(),
  useNavigate: jest.fn(),
}));

jest.mock('@mui/material/useMediaQuery');

jest.mock('./useCarouselState', () => ({
  useCarouselState: jest.fn().mockReturnValue({
    historyEvents: [],
    currentEventIndex: 0,
    setCurrentEventIndex: jest.fn(),
    loadMoreEvents: jest.fn(),
  }),
}));

// Mock Material-UI components
const mockIsDesktop = jest.fn();

jest.mock('@mui/material/Hidden', () => {
  return {
    __esModule: true,
    default: ({ children, mdUp, smDown }: { children: React.ReactNode; mdUp?: boolean; smDown?: boolean }) => {
      if (mdUp) {
        // Show content on mobile (when !mockIsDesktop())
        return !mockIsDesktop() ? <div data-testid="hidden-md-up">{children}</div> : null;
      }
      if (smDown) {
        // Show content on desktop (when mockIsDesktop())
        return mockIsDesktop() ? <div data-testid="hidden-sm-down">{children}</div> : null;
      }
      return null;
    },
  };
});

jest.mock('@mui/material/TextField', () => ({
  __esModule: true,
  default: (props: any) => (
    <div data-testid="mui-textfield">
      <label>{props.label}</label>
      <div className="input-wrapper">
        {props.InputProps?.startAdornment}
        <input {...props} className="fullwidth" />
      </div>
    </div>
  ),
}));

jest.mock('@mui/material/InputAdornment', () => ({
  __esModule: true,
  default: (props: any) => (
    <div data-testid="input-adornment" data-position={props.position}>
      {props.children}
    </div>
  ),
}));

jest.mock('@mui/icons-material/Search', () => ({
  __esModule: true,
  default: () => <span data-testid="search-icon">SearchIcon</span>,
}));

jest.mock('@mui/material/Typography', () => ({
  __esModule: true,
  default: (props: any) => (
    <h1 data-testid="mui-typography" data-variant={props.variant} style={props.sx}>
      {props.children}
    </h1>
  ),
}));

jest.mock('@mui/material/Divider', () => ({
  __esModule: true,
  default: (props: any) => <hr className="MuiDivider-root MuiDivider-fullWidth" style={props.sx} />,
}));

jest.mock('@mui/material/Autocomplete', () => ({
  __esModule: true,
  default: (props: any) => (
    <div className="MuiAutocomplete-root">
      {props.renderInput({
        ...props,
        InputProps: {
          ...props.InputProps,
          startAdornment: (
            <div data-testid="input-adornment" data-position="start">
              <span data-testid="search-icon">SearchIcon</span>
            </div>
          ),
        },
      })}
    </div>
  ),
}));

jest.mock('./carousel', () => ({
  __esModule: true,
  default: (props: any) => (
    <div data-testid="mock-carousel">
      {props.slides[props.startIndex]}
    </div>
  ),
}));

jest.mock('./eventView', () => ({
  __esModule: true,
  EventView: ({ event }: any) => (
    <div data-testid="mock-event-view">
      {event.text}
    </div>
  ),
}));

jest.mock('../../components/singleEntityMap', () => ({
  SingleEntityMap: ({ coords, size }: any) => (
    <div data-testid={`mock-map-${size.toLowerCase()}`}>
      Map with {coords.length} locations
    </div>
  ),
}));

describe('HistoryEventView', () => {
  const mockEvent = {
    id: '1',
    storyId: '1',
    storyTitle: 'The Life of Johann Bach',
    text: 'J.S. Bach was born in Eisenach on March 21st, 1685.',
    map: {
      locations: [
        {
          name: 'Eisenach',
          latitude: 50.9847,
          longitude: 10.3144,
        },
      ],
    },
    tags: [],
  };

  const renderWithRouter = (component: React.ReactNode) => {
    return render(
      <MemoryRouter initialEntries={['/']}>
        {component}
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    (useMediaQuery as jest.Mock).mockReset();
    mockIsDesktop.mockReset();
    const { useCarouselState } = require('./useCarouselState');
    (useCarouselState as jest.Mock).mockReset();
  });

  test('renders the history event view in desktop mode', async () => {
    (useMediaQuery as jest.Mock).mockReturnValue(true); // Desktop mode
    mockIsDesktop.mockReturnValue(true); // Desktop mode
    const { useCarouselState } = require('./useCarouselState');
    (useCarouselState as jest.Mock).mockReturnValue({
      historyEvents: [mockEvent],
      currentEventIndex: 0,
      setCurrentEventIndex: jest.fn(),
      loadMoreEvents: jest.fn(),
    });
    (useLoaderData as jest.Mock).mockReturnValue({
      events: [mockEvent],
      index: 0,
      loadNext: jest.fn(),
      loadPrev: jest.fn(),
    });

    renderWithRouter(<HistoryEventView />);

    // Check for common elements
    expect(screen.getByText('The Life of Johann Bach')).toBeInTheDocument();
    expect(screen.getByTestId('search-icon')).toBeInTheDocument();
    expect(screen.getByTestId('mock-carousel')).toBeInTheDocument();
    expect(screen.getByTestId('mock-event-view')).toBeInTheDocument();
    
    // In desktop mode:
    // - The desktop map should be in the second Grid item inside Hidden smDown
    // - The mobile map should not be rendered
    await waitFor(() => {
      const desktopMapContainer = screen.getByTestId('hidden-sm-down');
      expect(desktopMapContainer).toBeInTheDocument();
      expect(within(desktopMapContainer).getByTestId('mock-map-md')).toBeInTheDocument();
      expect(screen.queryByTestId('hidden-md-up')).not.toBeInTheDocument();
    });
  });

  test('renders the history event view in mobile mode', async () => {
    (useMediaQuery as jest.Mock).mockReturnValue(false); // Mobile mode
    mockIsDesktop.mockReturnValue(false); // Mobile mode
    const { useCarouselState } = require('./useCarouselState');
    (useCarouselState as jest.Mock).mockReturnValue({
      historyEvents: [mockEvent],
      currentEventIndex: 0,
      setCurrentEventIndex: jest.fn(),
      loadMoreEvents: jest.fn(),
    });
    (useLoaderData as jest.Mock).mockReturnValue({
      events: [mockEvent],
      index: 0,
      loadNext: jest.fn(),
      loadPrev: jest.fn(),
    });

    renderWithRouter(<HistoryEventView />);

    // Check for common elements
    expect(screen.getByText('The Life of Johann Bach')).toBeInTheDocument();
    expect(screen.getByTestId('search-icon')).toBeInTheDocument();
    expect(screen.getByTestId('mock-carousel')).toBeInTheDocument();
    expect(screen.getByTestId('mock-event-view')).toBeInTheDocument();
    
    // In mobile mode:
    // - The mobile map should be in the first Grid item inside Hidden mdUp
    // - The desktop map should not be rendered
    await waitFor(() => {
      const mobileMapContainer = screen.getByTestId('hidden-md-up');
      expect(mobileMapContainer).toBeInTheDocument();
      expect(within(mobileMapContainer).getByTestId('mock-map-sm')).toBeInTheDocument();
      expect(screen.queryByTestId('hidden-sm-down')).not.toBeInTheDocument();
    });
  });

  test('handles empty events array', () => {
    (useMediaQuery as jest.Mock).mockReturnValue(true);
    const { useCarouselState } = require('./useCarouselState');
    (useCarouselState as jest.Mock).mockReturnValue({
      historyEvents: [],
      currentEventIndex: 0,
      setCurrentEventIndex: jest.fn(),
      loadMoreEvents: jest.fn(),
    });
    (useLoaderData as jest.Mock).mockReturnValue({
      events: [],
      index: 0,
      loadNext: jest.fn(),
      loadPrev: jest.fn(),
    });

    renderWithRouter(<HistoryEventView />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders loading state when no events', () => {
    (useMediaQuery as jest.Mock).mockReturnValue(true);
    const { useCarouselState } = require('./useCarouselState');
    (useCarouselState as jest.Mock).mockReturnValue({
      historyEvents: [],
      currentEventIndex: 0,
      setCurrentEventIndex: jest.fn(),
      loadMoreEvents: jest.fn(),
    });
    (useLoaderData as jest.Mock).mockReturnValue({
      events: [],
      index: 0,
      loadNext: jest.fn(),
      loadPrev: jest.fn(),
    });

    renderWithRouter(<HistoryEventView />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('renders event view when events are present', () => {
    (useMediaQuery as jest.Mock).mockReturnValue(true);
    const { useCarouselState } = require('./useCarouselState');
    (useCarouselState as jest.Mock).mockReturnValue({
      historyEvents: [mockEvent],
      currentEventIndex: 0,
      setCurrentEventIndex: jest.fn(),
      loadMoreEvents: jest.fn(),
    });
    (useLoaderData as jest.Mock).mockReturnValue({
      events: [mockEvent],
      index: 0,
      loadNext: jest.fn(),
      loadPrev: jest.fn(),
    });

    renderWithRouter(<HistoryEventView />);
    expect(screen.getByText('The Life of Johann Bach')).toBeInTheDocument();
    expect(screen.getByText('J.S. Bach was born in Eisenach on March 21st, 1685.')).toBeInTheDocument();
  });
});