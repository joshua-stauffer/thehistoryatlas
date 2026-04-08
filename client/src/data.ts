import { HistoryEvent, Story } from "./graphql/events";

export const storyOfBach: Story = {
  id: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
  name: "The Life of Johann Sebastian Bach",
  events: [],
};
export const storyOfEisenach: Story = {
  id: "0a89653d-e6b3-448e-83e8-f9734b6d6b41",
  name: "The History of Eisenach",
  events: [],
};
export const storyOfMarch1685: Story = {
  id: "2931182b-d58c-4fbc-b31b-618a69197d7f",
  name: "The History of March 21st, 1685",
  events: [],
};
export const storyOfMarch1700: Story = {
  id: "a3d55990-8f18-4945-9dfb-32067d36802a",
  name: "The History of March 1700",
  events: [],
};
export const storyOfLuneburg: Story = {
  id: "a9a9cea5-ba22-4b7b-b8ae-29fe31fb8f4b",
  name: "The History of Lüneburg",
  events: [],
};

export const storyOfJuly1733: Story = {
  id: "21e37a98-9d90-49f9-8686-c4453873eda2",
  name: "The History of July 27th, 1733",
  events: [],
};

export const storyOfDresden: Story = {
  id: "2d564e3a-98a7-4b02-9822-a3e77a957f5d",
  name: "The History of Dresden",
  events: [],
};

export const stories: Story[] = [
  storyOfBach,
  storyOfMarch1700,
  storyOfLuneburg,
  storyOfMarch1685,
  storyOfEisenach,
  storyOfDresden,
  storyOfJuly1733,
];

export const bachIsBorn: HistoryEvent = {
  // first event
  id: "f423a520-006c-40d3-837f-a802fe299742",
  text: "J.S. Bach was born in Eisenach on March 21st, 1685.",
  lang: "en",
  date: {
    datetime: "1685-03-21 00:00:00",
    calendar: "http://www.wikidata.org/entity/Q1985727",
    precision: 11,
  },
  tags: [
    {
      id: "d815d481-c8bc-4be6-a687-d9aec46a7a64",
      type: "PERSON",
      name: "J. S. Bach",
      startChar: 0,
      stopChar: 9,
      defaultStoryId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
    {
      id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
      type: "PLACE",
      name: "Eisenach",
      startChar: 22,
      stopChar: 30,
      defaultStoryId: "0a89653d-e6b3-448e-83e8-f9734b6d6b41",
      location: {
        id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
        name: "Eisenach",
        latitude: 10.3147,
        longitude: 50.9796,
      },
    },
    {
      id: "7c4fa5a6-152d-403d-b3d1-5a586578dba4",
      type: "TIME",
      startChar: 34,
      stopChar: 50,
      name: "March 21st, 1685",
      time: "1685-03-21 00:00:00",
      calendar: "http://www.wikidata.org/entity/Q1985727",
      precision: 9,
      defaultStoryId: "2931182b-d58c-4fbc-b31b-618a69197d7f",
    },
  ],
  source: {
    id: "be42aa15-324b-4ed1-930f-456a64e9c55b",
    text: "In fact, for private purposes Bach had actually put down a bare outline of his professional career for a family Genealogy he was compiling around 1735: No. 24. Joh. Sebastian Bach, youngest son of Joh. Ambrosius Bach, was born in Eisenach in the year 1685 on March 21.",
    title: "Johann Sebastian Bach, The Learned Musician",
    author: "Wolff, Christoph",
    publisher: "W.W. Norton and Company",
    pubDate: "2000",
  },
  map: {
    locations: [
      {
        id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
        name: "Eisenach",
        longitude: 10.3147,
        latitude: 50.9796,
      },
    ],
  },
  focus: {
    id: "d815d481-c8bc-4be6-a687-d9aec46a7a64",
    name: "Johann Sebastian Bach",
    type: "PERSON",
  },
  storyTitle: storyOfBach.name,
  stories: [storyOfEisenach, storyOfBach, storyOfMarch1685],
};

export const bachArrivesInLuneburg: HistoryEvent = {
  id: "7f78b709-9037-45cb-b68c-e43894be7de0",
  text: "In March of 1700, J. S. Bach and Georg Erdmann arrived in Lüneburg to study at St. Michael's School.",
  lang: "en",
  date: {
    datetime: "1700-03-01 00:00:00",
    calendar: "http://www.wikidata.org/entity/Q1985727",
    precision: 10,
  },
  tags: [
    {
      id: "d815d481-c8bc-4be6-a687-d9aec46a7a64",
      type: "PERSON",
      name: "J. S. Bach",
      startChar: 18,
      stopChar: 28,
      defaultStoryId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
    {
      id: "3894ed48-76de-495b-b9ba-9edf1ba9c346",
      type: "PLACE",
      name: "Lüneburg",
      startChar: 58,
      stopChar: 66,
      location: {
        id: "3894ed48-76de-495b-b9ba-9edf1ba9c346",
        name: "Lüneburg",
        longitude: 10.41409,
        latitude: 53.2509,
      },
      defaultStoryId: "a9a9cea5-ba22-4b7b-b8ae-29fe31fb8f4b",
    },
    {
      id: "7c4fa5a6-152d-403d-b3d1-5a586578dba4",
      type: "TIME",
      startChar: 3,
      stopChar: 16,
      name: "March of 1700",
      time: "1700-03-01 00:00:00",
      calendar: "http://www.wikidata.org/entity/Q1985727",
      precision: 9,
      defaultStoryId: "a3d55990-8f18-4945-9dfb-32067d36802a",
    },
  ],
  source: {
    id: "be42aa15-324b-4ed1-930f-456a64e9c55b",
    text: "By whatever means of transportation, the two arrived in Lüneburg well before the end of March, as they were already singing in the choir of St. Michael’s School on April 3, the Saturday before Palm Sunday.",
    title: "Johann Sebastian Bach, The Learned Musician",
    author: "Wolff, Christoph",
    publisher: "W.W. Norton and Company",
    pubDate: "2000",
  },
  map: {
    locations: [
      {
        id: "3894ed48-76de-495b-b9ba-9edf1ba9c346",
        name: "Lüneburg",
        longitude: 10.41409,
        latitude: 53.2509,
      },
    ],
  },
  focus: {
    id: "d815d481-c8bc-4be6-a687-d9aec46a7a64",
    name: "Johann Sebastian Bach",
    type: "PERSON",
  },
  storyTitle: storyOfBach.name,
  stories: [storyOfBach, storyOfMarch1700, storyOfLuneburg],
};

export const bachDedicatesMass: HistoryEvent = {
  id: "3b518aad-2464-43c6-a991-050fc4eb0ac7",
  text: "On July 27th, 1733 J. S. Bach dedicated his Missa in B minor to the electoral court in Dresden",
  lang: "en",
  date: {
    datetime: "1733-07-27 00:00:00",
    calendar: "http://www.wikidata.org/entity/Q1985727",
    precision: 11,
  },
  tags: [
    {
      id: "d815d481-c8bc-4be6-a687-d9aec46a7a64",
      type: "PERSON",
      name: "J. S. Bach",
      startChar: 19,
      stopChar: 29,
      defaultStoryId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
    {
      id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
      type: "PLACE",
      name: "Dresden",
      startChar: 87,
      stopChar: 94,
      defaultStoryId: "2d564e3a-98a7-4b02-9822-a3e77a957f5d",
      location: {
        id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
        name: "Dresden",
        longitude: 13.73832,
        latitude: 51.05089,
      },
    },
    {
      id: "7c4fa5a6-152d-403d-b3d1-5a586578dba4",
      type: "TIME",
      startChar: 3,
      stopChar: 18,
      name: "July 27th, 1733",
      time: "1733-07-27 00:00:00",
      calendar: "http://www.wikidata.org/entity/Q1985727",
      precision: 11,
      defaultStoryId: "21e37a98-9d90-49f9-8686-c4453873eda2",
    },
  ],
  source: {
    id: "be42aa15-324b-4ed1-930f-456a64e9c55b",
    text: 'Not coincidentally, Bach found himself at work in 1733 on a special project that would occupy him for some time to come. On July 27 of that year, he dedicated to the elctoral court in Dresden the Missa in B minor -- the Kyrie and Gloria of what would become the B-minor Mass: "To your Royal Highness I submit in deepest devotion the present small work of that science which I have attained in musique."',
    title: "Johann Sebastian Bach, The Learned Musician",
    author: "Wolff, Christoph",
    publisher: "W.W. Norton and Company",
    pubDate: "2000",
  },
  map: {
    locations: [
      {
        id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
        name: "Dresden",
        longitude: 13.73832,
        latitude: 51.05089,
      },
    ],
  },
  focus: {
    id: "d815d481-c8bc-4be6-a687-d9aec46a7a64",
    name: "Johann Sebastian Bach",
    type: "PERSON",
  },
  storyTitle: storyOfBach.name,
  stories: [storyOfBach, storyOfJuly1733, storyOfDresden],
};

storyOfBach.events = [bachIsBorn, bachArrivesInLuneburg, bachDedicatesMass];
storyOfEisenach.events = [bachIsBorn];
storyOfMarch1685.events = [bachIsBorn];
storyOfMarch1700.events = [bachArrivesInLuneburg];
storyOfLuneburg.events = [bachArrivesInLuneburg];
storyOfJuly1733.events = [bachDedicatesMass];
storyOfDresden.events = [bachDedicatesMass];

export const events: HistoryEvent[] = [
  bachIsBorn,
  bachArrivesInLuneburg,
  bachDedicatesMass,
];
