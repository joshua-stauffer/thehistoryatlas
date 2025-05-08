import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
  within,
} from "@testing-library/react";
import { HistoryEventView } from "../historyEventView";
import {
  RouterProvider,
  createMemoryRouter,
  useRouteError,
} from "react-router-dom";
import { historyEventLoader } from "../historyEventLoader";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import "@testing-library/jest-dom";
import {
  debouncedSearchStories,
  StorySearchResponse,
  StorySearchResult,
} from "../../../api/stories";

// Mock event data
const mockEvent = {
  id: "f423a520-006c-40d3-837f-a802fe299742",
  text: "J. S. Bach was born in Eisenach on March 21st, 1685",
  lang: "en",
  date: {
    datetime: "1685-03-21",
    calendar: "gregorian",
    precision: 11,
  },
  source: {
    id: "source1",
    text: "Source text",
    title: "Bach Biography",
    author: "Author Name",
    publisher: "Publisher Name",
    pubDate: "2024-01-01",
  },
  tags: [
    {
      id: "tag1",
      type: "PERSON",
      startChar: 0,
      stopChar: 11,
      name: "J. S. Bach",
      defaultStoryId: "story1",
    },
  ],
  map: {
    locations: [
      {
        id: "loc1",
        latitude: 50.9847,
        longitude: 10.3089,
        name: "Eisenach",
      },
    ],
  },
  focus: null,
  storyTitle: "The Life of Bach",
  stories: [],
};

// Mock the loader
jest.mock("../historyEventLoader", () => ({
  historyEventLoader: jest
    .fn()
    .mockImplementation(async ({ params = {} } = { params: {} }) => {
      const loadNext = async (eventId: string) => {
        return [mockEvent];
      };
      const loadPrev = async (eventId: string) => {
        return [mockEvent];
      };
      const response = await fetch(`http://localhost:8000/api/history`);
      const data = await response.json();
      return {
        events: data.events,
        index: data.index,
        loadNext,
        loadPrev,
      };
    }),
}));

// Mock the carousel component
jest.mock("../carousel", () => ({
  __esModule: true,
  default: ({ slides }: { slides: JSX.Element[] }) => (
    <div data-testid="mock-carousel">{slides[0]}</div>
  ),
}));

// Mock SingleEntityMap component
jest.mock("../../../components/singleEntityMap", () => ({
  SingleEntityMap: () => <div data-testid="mock-map">Map</div>,
}));

// Mock fetch for API calls
global.fetch = jest.fn();

const mockSearchResults = {
  results: [
    { id: "1", name: "The Life of Bach" },
    { id: "2", name: "Classical Music History" },
    { id: "3", name: "German Composers" },
  ],
};

// Error Boundary Component
const ErrorBoundary = () => {
  const error = useRouteError();
  return (
    <div>
      <h2>Error</h2>
      <p>{error instanceof Error ? error.message : "Unknown error"}</p>
    </div>
  );
};

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const mockHistoryEvent = {
  id: "1",
  storyTitle: "The Life of Bach",
  date: {
    datetime: "1685-03-21",
    calendar: "gregorian",
    precision: 11,
  },
  map: {
    locations: [
      {
        name: "Leipzig",
        latitude: 51.3397,
        longitude: 12.3731,
      },
    ],
  },
  source: {
    id: "source1",
    text: "Source text",
    title: "Bach Biography",
    author: "Author Name",
    publisher: "Publisher Name",
    pubDate: "2024-01-01",
  },
  tags: [],
  stories: [],
  text: "J. S. Bach was born in Eisenach",
};

const createRouter = () => {
  return createMemoryRouter(
    [
      {
        path: "/",
        element: <HistoryEventView />,
        loader: () => ({
          events: [mockHistoryEvent],
          index: 0,
          loadNext: () => Promise.resolve(mockHistoryEvent),
          loadPrev: () => Promise.resolve(mockHistoryEvent),
        }),
      },
      {
        path: "/stories/:storyId",
        element: <HistoryEventView />,
        loader: () => ({
          events: [mockHistoryEvent],
          index: 0,
          loadNext: () => Promise.resolve(mockHistoryEvent),
          loadPrev: () => Promise.resolve(mockHistoryEvent),
        }),
      },
      {
        path: "/stories/:storyId/events/:eventId",
        element: <HistoryEventView />,
        loader: () => ({
          events: [mockHistoryEvent],
          index: 0,
          loadNext: () => Promise.resolve(mockHistoryEvent),
          loadPrev: () => Promise.resolve(mockHistoryEvent),
        }),
      },
    ],
    {
      initialEntries: ["/"],
    },
  );
};

// Mock the debounced search function
jest.mock("../../../api/stories", () => ({
  debouncedSearchStories: jest.fn(),
}));

const mockDebouncedSearchStories =
  debouncedSearchStories as jest.MockedFunction<typeof debouncedSearchStories>;

describe("Story Search Integration Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes("/api/stories/search")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              results: [{ id: "1", name: "The Life of Bach" }],
            }),
        });
      }
      return Promise.reject(new Error("Not found"));
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("displays search results when search button is clicked", async () => {
    // Mock the debounced search response
    mockDebouncedSearchStories.mockResolvedValueOnce({
      results: [{ id: "1", name: "The Life of Bach" }] as StorySearchResult[],
    } as StorySearchResponse);
    
    const router = createRouter();
    render(<RouterProvider router={router} />);

    // Type in the search box
    const searchInput = await screen.findByLabelText("Search for a story");
    fireEvent.change(searchInput, { target: { value: "Bach" } });
    
    // Click the search button
    const searchButton = screen.getByRole('button', { name: 'Search' });
    fireEvent.click(searchButton);

    // Wait for the option to appear
    await waitFor(
      () => {
        const option = screen.getByText("The Life of Bach");
        expect(option).toBeInTheDocument();
      },
      { timeout: 1000 },
    );
  });

  it("navigates to the correct story when selecting a search result", async () => {
    // Mock the debounced search response
    mockDebouncedSearchStories.mockResolvedValueOnce({
      results: [{ id: "1", name: "The Life of Bach" }] as StorySearchResult[],
    } as StorySearchResponse);

    const router = createRouter();
    render(<RouterProvider router={router} />);

    // Type in the search box and focus it
    const searchInput = await screen.findByLabelText("Search for a story");
    fireEvent.focus(searchInput);
    fireEvent.change(searchInput, { target: { value: "Bach" } });
    
    // Click the search button
    const searchButton = screen.getByRole('button', { name: 'Search' });
    fireEvent.click(searchButton);

    // Wait for the search results to be populated
    const option = await screen.findByRole(
      "option",
      { name: "The Life of Bach" },
      { timeout: 3000 },
    );
    expect(option).toBeInTheDocument();

    // Click the option (this will trigger navigation)
    fireEvent.click(option);

    // Wait for navigation
    expect(mockNavigate).toHaveBeenCalledWith("/stories/1");
  });

  it("disables search button when input is empty", async () => {
    const router = createRouter();
    render(<RouterProvider router={router} />);

    // Wait for the search input to appear first
    const searchInput = await screen.findByLabelText("Search for a story");
    
    // Find the search button (with a wait)
    const searchButton = await screen.findByRole('button', { name: 'Search' });
    
    // Check that button is initially disabled (empty input)
    expect(searchButton).toBeDisabled();
    
    // Type in the search box
    fireEvent.change(searchInput, { target: { value: "Bach" } });
    
    // Check that button is enabled
    expect(searchButton).not.toBeDisabled();
    
    // Clear the input
    fireEvent.change(searchInput, { target: { value: "" } });
    
    // Button should be disabled again
    expect(searchButton).toBeDisabled();
  });

  it("disables search button during search and shows loading indicator", async () => {
    // Mock a delayed search response
    mockDebouncedSearchStories.mockImplementationOnce(() => {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            results: [{ id: "1", name: "The Life of Bach" }] as StorySearchResult[],
          } as StorySearchResponse);
        }, 500);
      });
    });
    
    const router = createRouter();
    render(<RouterProvider router={router} />);

    // Type in the search box
    const searchInput = await screen.findByLabelText("Search for a story");
    fireEvent.change(searchInput, { target: { value: "Bach" } });
    
    // Click the search button
    const searchButton = screen.getByRole('button', { name: 'Search' });
    fireEvent.click(searchButton);
    
    // Button should be disabled while searching
    expect(searchButton).toBeDisabled();
    
    // CircularProgress should be visible
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    // Wait for search to complete
    await waitFor(
      () => {
        expect(searchButton).not.toBeDisabled();
      },
      { timeout: 1000 },
    );
  });

  it("handles empty search results", async () => {
    mockDebouncedSearchStories.mockResolvedValueOnce({
      results: [] as StorySearchResult[],
    } as StorySearchResponse);

    const router = createRouter();
    render(<RouterProvider router={router} />);

    // Type in the search box
    const searchInput = await screen.findByLabelText("Search for a story");
    fireEvent.change(searchInput, { target: { value: "Nonexistent" } });
    
    // Click the search button
    const searchButton = screen.getByRole('button', { name: 'Search' });
    fireEvent.click(searchButton);

    // Wait for the loading state to finish and verify no results
    await waitFor(() => {
      const listbox = screen.queryByRole("listbox");
      expect(listbox).not.toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    // Mock console.error
    const consoleErrorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    const error = new Error("API Error");

    // Mock the debounced search to throw an error
    mockDebouncedSearchStories.mockRejectedValueOnce(error);

    const router = createRouter();
    render(<RouterProvider router={router} />);

    // Type in the search box
    const searchInput = await screen.findByLabelText("Search for a story");
    fireEvent.change(searchInput, { target: { value: "Bach" } });
    
    // Click the search button
    const searchButton = screen.getByRole('button', { name: 'Search' });
    fireEvent.click(searchButton);

    // Wait for error to be logged
    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Failed to search stories:",
        error,
      );
    });

    // Verify no results are shown
    await waitFor(() => {
      const listbox = screen.queryByRole("listbox");
      expect(listbox).not.toBeInTheDocument();
    });

    consoleErrorSpy.mockRestore();
  });
});
