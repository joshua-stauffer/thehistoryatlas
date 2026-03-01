import React from "react";
import { render, act, waitFor, screen } from "@testing-library/react";
import { useNearbyEvents } from "../useNearbyEvents";
import { bachIsBorn, bachArrivesInLuneburg } from "../../../data";
import { NearbyEventsResponse } from "../../../api/nearbyEvents";
import { HistoryEvent } from "../../../graphql/events";

// Mock fetch
global.fetch = jest.fn();

const mockNearbyResponse: NearbyEventsResponse = {
  events: [
    {
      eventId: "abc-123",
      storyId: "story-456",
      personName: "Test Person",
      personDescription: "A test person",
      placeName: "Test Place",
      latitude: 51.0,
      longitude: 10.0,
      datetime: "+1685-06-15T00:00:00Z",
      precision: 9,
      calendarModel: "http://www.wikidata.org/entity/Q1985727",
    },
  ],
};

// Test component that exposes hook state
let hookResult: ReturnType<typeof useNearbyEvents>;

const TestComponent = ({ event }: { event: HistoryEvent | undefined }) => {
  hookResult = useNearbyEvents(event);
  return React.createElement("div", {
    "data-testid": "test",
    "data-count": hookResult.nearbyEvents.length,
    "data-loading": String(hookResult.isLoading),
  });
};

describe("useNearbyEvents", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockNearbyResponse),
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns empty array initially", () => {
    render(React.createElement(TestComponent, { event: bachIsBorn }));
    expect(hookResult.nearbyEvents).toEqual([]);
    expect(hookResult.isLoading).toBe(false);
  });

  it("fetches on loadNearbyEvents call", async () => {
    render(React.createElement(TestComponent, { event: bachIsBorn }));

    act(() => {
      hookResult.loadNearbyEvents({
        minLat: 50,
        maxLat: 52,
        minLng: 9,
        maxLng: 11,
      });
    });

    // Advance past debounce timer
    act(() => {
      jest.advanceTimersByTime(350);
    });

    await waitFor(() => {
      expect(hookResult.nearbyEvents).toHaveLength(1);
      expect(hookResult.nearbyEvents[0].personName).toBe("Test Person");
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/history/nearby"),
      expect.any(Object),
    );
  });

  it("clears when event changes", async () => {
    const { rerender } = render(
      React.createElement(TestComponent, { event: bachIsBorn }),
    );

    // Load some nearby events
    act(() => {
      hookResult.loadNearbyEvents({
        minLat: 50,
        maxLat: 52,
        minLng: 9,
        maxLng: 11,
      });
    });

    act(() => {
      jest.advanceTimersByTime(350);
    });

    await waitFor(() => {
      expect(hookResult.nearbyEvents).toHaveLength(1);
    });

    // Change to a different event
    rerender(
      React.createElement(TestComponent, { event: bachArrivesInLuneburg }),
    );

    await waitFor(() => {
      expect(hookResult.nearbyEvents).toEqual([]);
    });
  });

  it("handles errors gracefully", async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    render(React.createElement(TestComponent, { event: bachIsBorn }));

    act(() => {
      hookResult.loadNearbyEvents({
        minLat: 50,
        maxLat: 52,
        minLng: 9,
        maxLng: 11,
      });
    });

    act(() => {
      jest.advanceTimersByTime(350);
    });

    await waitFor(() => {
      expect(hookResult.isLoading).toBe(false);
    });

    expect(hookResult.nearbyEvents).toEqual([]);
    consoleSpy.mockRestore();
  });
});
