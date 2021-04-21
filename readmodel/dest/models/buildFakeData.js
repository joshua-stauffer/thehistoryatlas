"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const nameTag_1 = __importDefault(require("./nameTag"));
const uuid_1 = require("uuid");
const peopleNames = [
    // people names
    'Bach, Johann Sebastian',
    'Buxtehude, Deiterich',
    'Bach, Carl Philip Emmanuel',
    'Monteverdi, Claudio',
    'Castello, Dario',
    'Kerrl, Johann',
    'Farina, Carlo',
    // Bach is dynamically set later
];
const timeNames = [
    // time names
    // year:quarter:month:day
    '1600',
    '1625',
    '1649:3',
    '1670:3:8:25',
    '1693',
    '1699',
    '1712',
    '1721',
    '1730',
    '1745',
    '1746',
    '1753',
    '1759',
];
const placeNames = [
    // place names
    'Bologna',
    'Rome',
    'Venice',
    'Florence',
    'Vienna',
    'Paris',
    'Milan',
    'London'
];
const nameMap = new Map();
const allNames = [...peopleNames, ...timeNames, ...placeNames];
for (const name of allNames) {
    nameMap.set(name, [uuid_1.v4()]);
}
// show the ambiguity of two bachs
const b1 = nameMap.get('Bach, Johann Sebastian')[0];
const b2 = nameMap.get('Bach, Carl Philip Emmanuel')[0];
nameMap.set('Bach', [b1, b2]);
// add some names
const addNames = () => {
    const options = {
        upsert: true
    };
    for (const name of Object.keys(nameMap)) {
        const GUIDs = nameMap.get(name);
        nameTag_1.default.updateOne({ name: name }, {
            name: name,
            GUIDs: GUIDs
        }, options);
    }
};
// add some tags
// add some FocusSummaries
// run functions
addNames();
//# sourceMappingURL=buildFakeData.js.map