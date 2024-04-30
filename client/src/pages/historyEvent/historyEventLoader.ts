import { HistoryEvent, Story } from "../../graphql/events";
import { events, stories } from "../../data";
import { LoaderFunctionArgs } from "react-router-dom";
interface HistoryEventParams {
  storyId: string | undefined;
  eventId: string | undefined;
}

export interface HistoryEventData {
  events: HistoryEvent[];
  story: Story;
  index: number;
  currentEvent: HistoryEvent;
}

type EventsAndStories = {
  events: HistoryEvent[];
  stories: Story[];
};

const buildFakeData: EventsAndStories = () => {
  faker.seed(123);
};

const eventMap = new Map<string, HistoryEvent>([]);
events.map((historyEvent) => {
  eventMap.set(historyEvent.id, historyEvent);
});

const storyMap = new Map<string, Story>([]);
stories.map((story) => {
  storyMap.set(story.id, story);
});

export const historyEventLoader = ({
  params: { eventId, storyId },
}: LoaderFunctionArgs): HistoryEventData => {
  if (eventId === undefined || storyId === undefined) {
    throw new Error("eventId and storyId are required parameters.");
  }
  const story = storyMap.get(storyId);
  if (story === undefined) {
    throw new Error("Story not found");
  }
  const currentEvent = eventMap.get(eventId);
  if (currentEvent === undefined) {
    throw new Error("Event not found");
  }
  const eventIndex = story.events.findIndex(
    (historyEvent) => historyEvent.id === currentEvent.id
  );
  const nextEvent: HistoryEvent | null = story.events[eventIndex + 1] || null;
  let index = 1;
  let prevEvent: HistoryEvent | null;
  if (eventIndex === 0) {
    // no previous event
    index = 0;
    prevEvent = null;
  } else {
    prevEvent = story.events[eventIndex - 1] || null;
  }
  const maybeEvents = [prevEvent, currentEvent, nextEvent];
  const events: HistoryEvent[] = [];
  for (const event of maybeEvents) {
    if (event) {
      events.push(event);
    }
  }
  return { events, story, index, currentEvent };
};
