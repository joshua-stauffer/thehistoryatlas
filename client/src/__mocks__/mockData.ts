import { HistoryEvent, Story } from "../graphql/events";
import { HistoryEventData } from "../pages/historyEvent/historyEventLoader";
import { v4 as uuidv4 } from 'uuid';

// Helper function to create a mock UUID if needed
const createMockId = () => uuidv4();

// Create mock data based on the REST API structure
export const mockStory: Story = {
  id: "mock-story-1",
  name: "The Life of Johann Bach",
  events: [], // Will be populated later
};

export const mockHistoryEvent: HistoryEvent = {
  id: "mock-event-1",
  text: "J.S. Bach was born in Eisenach on March 21st, 1685.",
  lang: "en",
  date: {
    datetime: "1685-03-21 00:00:00",
    calendar: "gregorian",
    precision: 11,
  },
  tags: [
    {
      id: "mock-tag-1",
      type: "PERSON",
      name: "J.S. Bach",
      startChar: 0,
      stopChar: 9,
      defaultStoryId: mockStory.id,
    },
    {
      id: "mock-tag-2",
      type: "PLACE",
      name: "Eisenach",
      startChar: 22,
      stopChar: 30,
      defaultStoryId: "mock-story-2",
      location: {
        id: "mock-location-1",
        name: "Eisenach",
        latitude: 50.9796,
        longitude: 10.3147,
      },
    },
    {
      id: "mock-tag-3",
      type: "TIME",
      startChar: 34,
      stopChar: 50,
      name: "March 21st, 1685",
      time: "1685-03-21 00:00:00",
      calendar: "gregorian",
      precision: 11,
      defaultStoryId: "mock-story-3",
    },
  ],
  source: {
    id: "mock-source-1",
    text: "Johann Sebastian Bach was born in Eisenach in the year 1685 on March 21.",
    title: "Johann Sebastian Bach, The Learned Musician",
    author: "Wolff, Christoph",
    publisher: "W.W. Norton and Company",
    pubDate: "2000",
  },
  map: {
    locations: [
      {
        id: "mock-location-1",
        name: "Eisenach",
        longitude: 10.3147,
        latitude: 50.9796,
      },
    ],
  },
  focus: {
    id: "mock-focus-1",
    name: "Johann Sebastian Bach",
    type: "PERSON",
  },
  storyTitle: mockStory.name,
  stories: [{ ...mockStory, events: [] }],
};

export const mockHistoryEvent2: HistoryEvent = {
  id: "mock-event-2",
  text: "In March of 1700, J.S. Bach arrived in Lüneburg to study.",
  lang: "en",
  date: {
    datetime: "1700-03-01 00:00:00",
    calendar: "gregorian",
    precision: 10,
  },
  tags: [
    {
      id: "mock-tag-4",
      type: "PERSON",
      name: "J.S. Bach",
      startChar: 18,
      stopChar: 27,
      defaultStoryId: mockStory.id,
    },
    {
      id: "mock-tag-5",
      type: "PLACE",
      name: "Lüneburg",
      startChar: 37,
      stopChar: 45,
      defaultStoryId: "mock-story-4",
      location: {
        id: "mock-location-2",
        name: "Lüneburg",
        latitude: 53.2509,
        longitude: 10.41409,
      },
    },
    {
      id: "mock-tag-6",
      type: "TIME",
      startChar: 3,
      stopChar: 16,
      name: "March of 1700",
      time: "1700-03-01 00:00:00",
      calendar: "gregorian",
      precision: 10,
      defaultStoryId: "mock-story-5",
    },
  ],
  source: {
    id: "mock-source-2",
    text: "Bach arrived in Lüneburg in March of 1700 to study at St. Michael's School.",
    title: "Johann Sebastian Bach, The Learned Musician",
    author: "Wolff, Christoph",
    publisher: "W.W. Norton and Company",
    pubDate: "2000",
  },
  map: {
    locations: [
      {
        id: "mock-location-2",
        name: "Lüneburg",
        longitude: 10.41409,
        latitude: 53.2509,
      },
    ],
  },
  focus: {
    id: "mock-focus-2",
    name: "Johann Sebastian Bach",
    type: "PERSON",
  },
  storyTitle: mockStory.name,
  stories: [{ ...mockStory, events: [] }],
};

// Create mock events array
export const mockEvents: HistoryEvent[] = [mockHistoryEvent, mockHistoryEvent2];

// Populate the story's events
mockStory.events = mockEvents;

// Create mock loader data
export const mockHistoryEventData: HistoryEventData = {
  events: mockEvents,
  index: 0,
  loadNext: jest.fn().mockResolvedValue(mockEvents),
  loadPrev: jest.fn().mockResolvedValue(mockEvents),
}; 