import { HistoryEvent } from "../../graphql/events";
import { events } from "../../data";
import { LoaderFunctionArgs } from "react-router-dom";

interface HistoryEventLoaderProps {
  params: HistoryEventParams;
}

interface HistoryEventParams {
  storyId: string | undefined;
  eventId: string | undefined;
}

export interface HistoryEventData {
  event: HistoryEvent;
}

const eventData: Map<string, Map<string, HistoryEvent>> = new Map();
for (const event of events) {
  const event_id = event.id;
  const story_id = event.story.id;
  const storyEntry = eventData.get(event.story.id);
  if (!!storyEntry) {
    storyEntry.set(event_id, event);
  } else {
    const eventMap = new Map<string, HistoryEvent>([[event_id, event]]);
    eventData.set(story_id, eventMap);
  }
}

export const historyEventLoader = ({
  params: { eventId, storyId },
}: LoaderFunctionArgs): HistoryEventData => {
  if (eventId === undefined || storyId === undefined) {
    throw new Error("eventId and storyId are required parameters.");
  }
  const storyMap = eventData.get(storyId);
  if (storyMap === undefined) {
    throw new Error("Story not found");
  }
  const event = storyMap.get(eventId);
  if (event === undefined) {
    throw new Error("Event not found");
  }
  return { event };
};
