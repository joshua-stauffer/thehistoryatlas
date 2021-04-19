

const { gql } = require('apollo-server')

export const typeDefs = gql`

  type Query {

    FocusSummary(
      focusType: FocusType!
      focusGUID: String!
      ): [TimeTagSummary]

    TimeTagDetails(
      focusGUID: String!
      timeTagGUID: String!
    ): [Citation]!

  }

  type TimeTagSummary {
    timeTag: String!
    GUID: String!
    citationCount: Int!
  }

  type Citation {
    text: String!
    tags: [Tag!]!
    meta: MetaData!
  }

  type Tag {
    type: FocusType!
    GUID: String!    # which entity does this tag refer to?
    start: Int!      # index of character in text 
    end: Int!        # index of character in text 
  }

  type MetaData {
    author: String!
    publisher: String!
    pubDate: String
    pageNum: Int
  }

  enum FocusType {
    TIME
    PERSON
    PLACE
  }

`

/*
  MapView {
    timeTagGUID: String!
    BoundingBox!: BoundingBox
  }



  type PlaceSummaryByTimeTag {
    placeName: [ String ]
    placeLocation: Location
    citationCount: Int
    personCount: Int
  }

  type TimeTagByFocus {
    citations: [Citation]
    adjacentPeople: [Person]
  }

  type Location {
    point: Point
    shape: [ Point ]
  }

  type Point {
    latitude: Float
    longitude: Float
  }

  type BoundingBox {
    upperLeft: Point
    lowerRight: Point
  }







  type Person {
    guid: String
    names: [String]
  }

  type Name {
    name: String
    guid: String
  }

  type Query {


    getName(
      guid: String
    ): String
  }

  enum Direction {
    # Which direction in time are we headed?
    FUTURE
    PAST
  }


*/