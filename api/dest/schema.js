"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.typeDefs = void 0;
const { gql } = require('apollo-server');
exports.typeDefs = gql `


  type PlaceSummaryByTimeTag {
    placeName: [ String ]
    placeLocation: Location
    citationCount: Int
    personCount: Int
  }

  type Location {
    point: Point
    shape: [ Point ]
  }

  type Point {
    latitude: Float
    longitude: Float
  }

  type Query {
    placeSummary: [PlaceSummaryByTimeTag]
  }

`;
/*
  type Person {
    guid: String
    names: [String]
    orderedTimeTags: [String]
  }

  type Query {
    Map: [Person]
  }

  type Name {
    name: String
    guid: [String]
  }

  type Query {
    name: [Name]
  }

  type Place {
    guid: String
    names: [String]
    location: Location
  }



*/ 
//# sourceMappingURL=schema.js.map