import { historyEventLoader } from './historyEventLoader';
import { mockHistoryEvent, mockHistoryEvent2 } from '../../__mocks__/mockData';

// Mock the global fetch function
global.fetch = jest.fn();

describe('historyEventLoader', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    
    // Setup default fetch response
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        events: [mockHistoryEvent, mockHistoryEvent2],
        index: 0
      })
    });
  });

  test('loads history events with no parameters', async () => {
    const result = await historyEventLoader({ params: {} });
    
    // Check that fetch was called with the correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/history?',
      // Other server URL could be:
      // 'https://the-history-atlas-server-4ubzi.ondigitalocean.app/api/history?'
    );
    
    // Check that the result contains the expected data
    expect(result).toEqual({
      events: [mockHistoryEvent, mockHistoryEvent2],
      index: 0,
      loadNext: expect.any(Function),
      loadPrev: expect.any(Function),
    });
  });

  test('loads history events with storyId parameter', async () => {
    const storyId = 'mock-story-1';
    const result = await historyEventLoader({ params: { storyId } });
    
    // Check that fetch was called with the correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      `http://localhost:8000/api/history?storyId=${storyId}`,
    );
    
    // Check that the result contains the expected data
    expect(result).toEqual({
      events: [mockHistoryEvent, mockHistoryEvent2],
      index: 0,
      loadNext: expect.any(Function),
      loadPrev: expect.any(Function),
    });
  });

  test('loads history events with eventId parameter', async () => {
    const eventId = 'mock-event-1';
    const result = await historyEventLoader({ params: { eventId } });
    
    // Check that fetch was called with the correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      `http://localhost:8000/api/history?eventId=${eventId}`,
    );
    
    // Check that the result contains the expected data
    expect(result).toEqual({
      events: [mockHistoryEvent, mockHistoryEvent2],
      index: 0,
      loadNext: expect.any(Function),
      loadPrev: expect.any(Function),
    });
  });

  test('loads history events with both storyId and eventId parameters', async () => {
    const storyId = 'mock-story-1';
    const eventId = 'mock-event-1';
    const result = await historyEventLoader({ params: { storyId, eventId } });
    
    // Check that fetch was called with the correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      `http://localhost:8000/api/history?storyId=${storyId}&eventId=${eventId}`,
    );
    
    // Check that the result contains the expected data
    expect(result).toEqual({
      events: [mockHistoryEvent, mockHistoryEvent2],
      index: 0,
      loadNext: expect.any(Function),
      loadPrev: expect.any(Function),
    });
  });

  test('loadNext function works correctly', async () => {
    const result = await historyEventLoader({ params: {} });
    
    // Reset mock to track the next call
    (global.fetch as jest.Mock).mockClear();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        events: [mockHistoryEvent2],
        index: 0
      })
    });
    
    // Call loadNext with an eventId
    await result.loadNext('mock-event-1');
    
    // Check that fetch was called with the correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/history?eventId=mock-event-1&direction=next',
    );
  });

  test('loadPrev function works correctly', async () => {
    const result = await historyEventLoader({ params: {} });
    
    // Reset mock to track the next call
    (global.fetch as jest.Mock).mockClear();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        events: [mockHistoryEvent],
        index: 0
      })
    });
    
    // Call loadPrev with an eventId
    await result.loadPrev('mock-event-2');
    
    // Check that fetch was called with the correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/history?eventId=mock-event-2&direction=prev',
    );
  });

  test('throws error when fetch fails', async () => {
    // Mock a failed fetch response
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
    });
    
    // Expect the historyEventLoader to throw an error
    await expect(historyEventLoader({ params: {} })).rejects.toThrow(
      'Failed to fetch history events'
    );
  });
}); 