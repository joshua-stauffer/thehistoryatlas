import { HistoryEvent, PeopleAndPlaceOption } from "./graphql/events";

export const events: HistoryEvent[] = [
  {
    id: "3b518aad-2464-43c6-a991-050fc4eb0ac7",
    story: {
      id: "21e37a98-9d90-49f9-8686-c4453873eda2",
      name: "The History of July 27th, 1733",
    },
    text: "On July 27th, 1733 J. S. Bach dedicated his Missa in B minor to the electoral court in Dresden",
    lang: "en",
    date: {
      time: "1733-07-27 00:00:00",
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

    relatedStories: [
      {
        id: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
        name: "The Life of Johann Sebastian Bach",
      },
      {
        id: "2d564e3a-98a7-4b02-9822-a3e77a957f5d",
        name: "The History of Dresden",
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
    id: "3b518aad-2464-43c6-a991-050fc4eb0ac7",
    story: {
      id: "2d564e3a-98a7-4b02-9822-a3e77a957f5d",
      name: "The History of Dresden",
    },
    text: "On July 27th, 1733 J. S. Bach dedicated his Missa in B minor to the electoral court in Dresden",
    lang: "en",
    date: {
      time: "1733-07-27 00:00:00",
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

    relatedStories: [
      {
        id: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
        name: "The Life of Johann Sebastian Bach",
      },
      {
        id: "21e37a98-9d90-49f9-8686-c4453873eda2",
        name: "The History of July 27th, 1733",
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
    id: "3b518aad-2464-43c6-a991-050fc4eb0ac7",
    story: {
      id: "9df8f0a3-cd99-4443-bb08-98d901dc363e",
      name: "The Life of Johann Sebastian Bach",
    },
    text: "On July 27th, 1733 J. S. Bach dedicated his Missa in B minor to the electoral court in Dresden",
    lang: "en",
    date: {
      time: "1733-07-27 00:00:00",
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
    relatedStories: [
      {
        id: "2d564e3a-98a7-4b02-9822-a3e77a957f5d",
        name: "The History of Dresden",
      },
      {
        id: "21e37a98-9d90-49f9-8686-c4453873eda2",
        name: "The History of July 27th, 1733",
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
    id: "58679bfb-a534-4d9e-a577-9e8da8373017",
    text: "",
    lang: "en",
    date: {
      time: "",
      calendar: "http://www.wikidata.org/entity/Q1985727",
      precision: 11,
    },
    tags: [],
    source: {
      id: "be42aa15-324b-4ed1-930f-456a64e9c55b",
      text: "",
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
      id: "3b518aad-2464-43c6-a991-050fc4eb0ac7",
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
      id: "3b518aad-2464-43c6-a991-050fc4eb0ac7",
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
