import { HistoryEvent, PeopleAndPlaceOption } from "./graphql/events";

export const events: HistoryEvent[] = [
  {
    id: "f423a520-006c-40d3-837f-a802fe299742",
    text: "J.S. Bach was born in Eisenach on March 21st, 1685.",
    lang: "en",
    date: {
      time: "1685-03-21 00:00:00",
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
    story: {
      id: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
      name: "The Life of Johann Sebastian Bach",
    },
    relatedStories: [
      {
        id: "0a89653d-e6b3-448e-83e8-f9734b6d6b41",
        name: "The History of Eisenach",
      },
      {
        id: "2931182b-d58c-4fbc-b31b-618a69197d7f",
        name: "The History of March 21st, 1685",
      },
    ],
    prevEvent: {
      id: "f423a520-006c-40d3-837f-a802fe299742",
      storyId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
    nextEvent: {
      id: "f423a520-006c-40d3-837f-a802fe299742",
      storyId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
  },
  {
    id: "f423a520-006c-40d3-837f-a802fe299742",
    text: "J.S. Bach was born in Eisenach on March 21st, 1685.",
    lang: "en",
    date: {
      time: "1685-03-21 00:00:00",
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
        location: {
          id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
          name: "Eisenach",
          latitude: 10.3147,
          longitude: 50.9796,
        },
        defaultStoryId: "0a89653d-e6b3-448e-83e8-f9734b6d6b41",
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
    story: {
      id: "2931182b-d58c-4fbc-b31b-618a69197d7f",
      name: "The History of March 21st, 1685",
    },
    relatedStories: [
      {
        id: "0a89653d-e6b3-448e-83e8-f9734b6d6b41",
        name: "The History of Eisenach",
      },
      {
        id: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
        name: "The Life of Johann Sebastian Bach",
      },
    ],
    prevEvent: {
      id: "f423a520-006c-40d3-837f-a802fe299742",
      storyId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
    nextEvent: {
      id: "f423a520-006c-40d3-837f-a802fe299742",
      storyId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
  },
  {
    id: "f423a520-006c-40d3-837f-a802fe299742",
    text: "J.S. Bach was born in Eisenach on March 21st, 1685.",
    lang: "en",
    date: {
      time: "1685-03-21 00:00:00",
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
        location: {
          id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
          name: "Eisenach",
          latitude: 10.3147,
          longitude: 50.9796,
        },
        defaultStoryId: "0a89653d-e6b3-448e-83e8-f9734b6d6b41",
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
    story: {
      id: "0a89653d-e6b3-448e-83e8-f9734b6d6b41",
      name: "The History of Eisenach",
    },
    relatedStories: [
      {
        id: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
        name: "The Life of Johann Sebastian Bach",
      },
      {
        id: "2931182b-d58c-4fbc-b31b-618a69197d7f",
        name: "The History of March 21st, 1685",
      },
    ],
    prevEvent: {
      id: "f423a520-006c-40d3-837f-a802fe299742",
      storyId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
    nextEvent: {
      id: "f423a520-006c-40d3-837f-a802fe299742",
      storyId: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
    },
  },
];

export const peopleAndPlaceOptions: PeopleAndPlaceOption[] = [
  {
    id: "d815d481-c8bc-4be6-a687-d9aec46a7a64",
    name: "Johann Sebastian Bach",
    type: "PERSON",
  },
  {
    id: "1318e533-80e0-4f2b-bd08-ae7150ffee86",
    name: "Eisenach",
    type: "PLACE",
  },
];
