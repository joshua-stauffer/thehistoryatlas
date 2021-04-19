"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.timeTagDetails = exports.personSummaryData = void 0;
const uuid_1 = require("uuid");
// fake focus summary data
// three tables: person, place,t ime
const BachGUID = uuid_1.v4();
const BuxtGUID = uuid_1.v4();
const tt1650 = uuid_1.v4();
const tt1668 = uuid_1.v4();
const tt1679 = uuid_1.v4();
const tt1685 = uuid_1.v4();
const tt1703 = uuid_1.v4();
const tt1750 = uuid_1.v4();
const buxt1650 = tt1650 + BuxtGUID;
const buxt1668 = tt1668 + BuxtGUID;
const buxt1679 = tt1679 + BuxtGUID;
const buxt1685 = tt1685 + BuxtGUID;
const buxt1703 = tt1703 + BuxtGUID;
const bach1685 = tt1685 + BachGUID;
const bach1703 = tt1703 + BachGUID;
const bach1750 = tt1750 + BachGUID;
exports.personSummaryData = [
    {
        GUID: BachGUID,
        timeTagSummaries: [
            {
                timeTag: '1685',
                GUID: tt1685,
                citationCount: 1
            },
            {
                timeTag: '1703',
                GUID: tt1703,
                citationCount: 3
            },
            {
                timeTag: '1750:3:7:28',
                GUID: tt1750,
                citationCount: 2
            }
        ]
    },
    {
        GUID: BuxtGUID,
        timeTagSummaries: [
            {
                timeTag: '1650',
                GUID: tt1650,
                citationCount: 1
            },
            {
                timeTag: '1668',
                GUID: tt1668,
                citationCount: 1
            },
            {
                timeTag: '1679',
                GUID: tt1679,
                citationCount: 1
            },
            {
                timeTag: '1685',
                GUID: tt1685,
                citationCount: 1
            },
            {
                timeTag: '1703',
                GUID: tt1703,
                citationCount: 1
            }
        ]
    }
];
console.log(exports.personSummaryData);
exports.timeTagDetails = [
    {
        GUID: buxt1650,
        citations: [
            {
                text: 'Sometime around here buxtehude was born',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    },
    {
        GUID: buxt1668,
        citations: [
            {
                text: 'Sometime around here buxtehude did something else',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    },
    {
        GUID: buxt1679,
        citations: [
            {
                text: 'Sometime around here buxtehude was born',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    },
    {
        GUID: buxt1685,
        citations: [
            {
                text: 'Sometime around here buxtehude did something else',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    },
    {
        GUID: buxt1703,
        citations: [
            {
                text: 'Sometime around here buxtehude was born',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    },
    {
        GUID: bach1685,
        citations: [
            {
                text: 'Sometime around here Bach was born',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    },
    {
        GUID: bach1703,
        citations: [
            {
                text: 'Sometime around here bach did something',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            },
            {
                text: 'Sometime around here bach did something else',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            },
            {
                text: 'Now Something Else!',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    },
    {
        GUID: bach1750,
        citations: [
            {
                text: 'Sometime around here bach died',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            },
            {
                text: 'We agree that bach died',
                tags: [
                    {
                        type: 'PERSON',
                        GUID: uuid_1.v4(),
                        start: 23,
                        end: 29
                    }
                ],
                meta: {
                    author: "someone",
                    publisher: "a publisher"
                }
            }
        ]
    }
];
console.log(exports.timeTagDetails);
//# sourceMappingURL=fakeData.js.map