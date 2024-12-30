import { HistoryEvent } from "../../graphql/events";

export interface HistoryEventData {
  events: HistoryEvent[];
  index: number;
  loadNext: () => Promise<HistoryEvent[]>;
  loadPrev: () => Promise<HistoryEvent[]>;
}

export const historyEventLoader = async ({
  params,
}: {
  params: { storyId?: string; eventId?: string };
}) => {
  const fetchEvents = async (
    storyId?: string,
    eventId?: string,
    direction?: "next" | "prev"
  ) => {
    const queryParams = new URLSearchParams();
    if (storyId) queryParams.append("storyId", storyId);
    if (eventId) queryParams.append("eventId", eventId);
    if (direction) queryParams.append("direction", direction);

    const response = await fetch(
      `https://the-history-atlas-server-4ubzi.ondigitalocean.app/api/history?${queryParams.toString()}`
    );
    if (!response.ok) {
      throw new Error("Failed to fetch history events");
    }
    return await response.json();
  };

  const loadNext = async (eventId: string) => {
    const response = await fetchEvents(params.storyId, eventId, "next");
    return response.events;
  };

  const loadPrev = async (eventId: string) => {
    const response = await fetchEvents(params.storyId, eventId, "prev");
    return response.events;
  };

  // Fetch initial data
  const initialData = await fetchEvents(params.storyId, params.eventId);

  // Return data along with loadNext and loadPrev
  return {
    events: initialData.events,
    index: initialData.index,
    loadNext,
    loadPrev,
  };
};
