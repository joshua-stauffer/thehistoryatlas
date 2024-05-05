import {
  CalendarDate,
  Focus,
  HistoryEvent,
  Person,
  Place,
  Point,
  Source,
  Story,
  Tag,
  Time,
} from "../../graphql/events";
import { events, stories } from "../../data";
import { LoaderFunctionArgs } from "react-router-dom";
import { faker } from "@faker-js/faker";
import { PersonTag, PlaceTag, TimeTag } from "../../types";
import {
  renderDateTime,
  renderDay,
} from "../../components/renderDateTime/time";
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

const fakeEventMap = new Map<string, HistoryEvent>([]);
const fakeStoryMap = new Map<string, Story>([]);

faker.seed(872);

export const fakeHistoryEventLoader = ({
  params: { eventId, storyId },
}: LoaderFunctionArgs): HistoryEventData => {
  const { story, events, index } = buildStoryAndEvents();
  return {
    story: story,
    events: events,
    index: index,
    currentEvent: events[index],
  };
};

type StoryAndEvents = {
  story: Story;
  events: HistoryEvent[];
  index: number;
};

const buildStoryAndEvents = (): StoryAndEvents => {
  const { events, index } = buildEvents();

  const story = buildStory(events);
  return {
    events,
    story,
    index,
  };
};

type BuiltEvents = {
  events: HistoryEvent[];
  index: number;
};

const buildEvents = (): BuiltEvents => {
  const eventCount = 20;
  const mapOptions = {
    name: faker.location.city(),
    latitude: faker.location.latitude(),
    longitude: faker.location.longitude(),
  };
  const dateOptions = {
    date: faker.date.past(),
    exact: false,
    storyLengthInYears: 60,
  };

  let eventList: HistoryEvent[] = [];
  for (let i = 0; i < eventCount; i++) {
    eventList.push(buildEvent(dateOptions, mapOptions));
  }
  const exactDateOptions = {
    ...dateOptions,
    exact: true,
  };

  const index = Math.floor(eventCount / 2);
  const focusedEvent = buildEvent(exactDateOptions, mapOptions);
  eventList = [
    ...eventList.slice(0, index),
    focusedEvent,
    ...eventList.slice(index),
  ];
  return { events: eventList, index: index };
};

const buildStory = (events: HistoryEvent[]): Story => {
  const timeName = renderDateTime({
    calendar: "fake",
    time: String(faker.date.past()),
    precision: 11,
  });

  const storyTemplates = [
    () => `The life of ${faker.person.fullName()}.`,
    () => `The history of ${timeName}.`,
    () => `The history of ${faker.location.city()}.`,
  ];
  const randomStoryTitle =
    storyTemplates[Math.floor(Math.random() * storyTemplates.length)];
  return {
    id: faker.string.uuid(),
    name: randomStoryTitle(),
    events: events,
  };
};

type DateOptions = {
  date: Date;
  exact: boolean;
  storyLengthInYears: number;
};

const buildDate = (options: DateOptions): Date => {
  return options.exact
    ? options.date
    : faker.date.anytime({
        refDate: options.date,
      });
};

type MapOptions = {
  longitude: number;
  latitude: number;
  name: string;
};

const buildMap = (options: MapOptions): Point[] => {
  const maximumExtraPlaces = 10;
  const minimumExtraPlaces = 3;
  let mapCount = Math.floor(Math.random() * maximumExtraPlaces);
  if (mapCount < minimumExtraPlaces) {
    mapCount = minimumExtraPlaces;
  }
  const points: Point[] = [];
  for (let i = 0; i < mapCount; i++) {
    points.push(createPoint(options));
  }

  return points;
};

const createPoint = (options: MapOptions): Point => {
  const [latitude, longitude] = faker.location.nearbyGPSCoordinate({
    origin: [options.latitude, options.longitude],
  });
  return {
    latitude: latitude,
    longitude: longitude,
    id: faker.string.uuid(),
    name: faker.location.city(),
  };
};

const buildSource = (): Source => {
  return {
    id: faker.string.uuid(),
    text: faker.lorem.paragraph(),
    title: faker.lorem.sentence(),
    author: faker.person.fullName(),
    publisher: faker.company.name(),
    pubDate: String(faker.date.recent()),
  };
};

type BuiltTags = {
  tags: Tag[];
  taggedText: string;
};

const buildTags = (
  text: string,
  dateOptions: DateOptions,
  mapOptions: MapOptions
): BuiltTags => {
  const personName = faker.person.fullName();
  const point = createPoint(mapOptions);
  const date = buildDate(dateOptions);
  const timeName = renderDay(date);

  const insertWord = (
    splitText: string[],
    word: string,
    index: number
  ): string[] => {
    return [...splitText.slice(0, index), word, ...splitText.slice(index)];
  };

  let splitText = text.split(" ");
  splitText = insertWord(splitText, personName, 0);
  splitText = insertWord(splitText, point.name, 2);
  splitText = insertWord(splitText, timeName, 4);
  const taggedText = splitText.join(" ");
  const person: Person = {
    type: "PERSON",
    id: faker.string.uuid(),
    startChar: taggedText.indexOf(personName),
    stopChar: taggedText.indexOf(personName) + personName.length,
    name: personName,
    defaultStoryId: faker.string.uuid(),
  };
  const personStory = {};
  const place: Place = {
    id: point.id,
    type: "PLACE",
    startChar: taggedText.indexOf(point.name),
    stopChar: taggedText.indexOf(point.name) + point.name.length,
    name: point.name,
    location: point,
    defaultStoryId: faker.string.uuid(),
  };
  const time: Time = {
    id: faker.string.uuid(),
    type: "TIME",
    startChar: taggedText.indexOf(timeName),
    stopChar: taggedText.indexOf(timeName) + timeName.length,
    name: timeName,
    time: String(date),
    calendar: "gregorian",
    precision: 11, // day precision
    defaultStoryId: faker.string.uuid(),
  };
  return {
    tags: [person, place, time],
    taggedText: taggedText,
  };
};

function buildEvent(
  dateOptions: DateOptions,
  mapOptions: MapOptions
): HistoryEvent {
  const text = faker.lorem.sentence();
  const { tags, taggedText } = buildTags(text, dateOptions, mapOptions);

  return {
    id: faker.string.uuid(),
    text: taggedText,
    lang: "lorem",
    date: {
      time: String(buildDate(dateOptions)),
      calendar: "gregorian",
      precision: 11,
    },
    source: buildSource(),
    tags: tags,
    map: {
      locations: buildMap(mapOptions),
    },
    focus: null,
    stories: [],
  };
}
