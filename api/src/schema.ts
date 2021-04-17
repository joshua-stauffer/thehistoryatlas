

const { gql } = require('apollo-server')

export const typeDefs = gql`


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

  type Citation {
    text: String
    tags: [Tag]
    meta: MetaData
  }

  type Tag {
    type: FocusType!
    guid: String!    # which entity does this tag refer to?
    start: Int!      # index of character in text 
    end: Int!        # index of character in text 
  }

  MetaData {
    author: String!
    publisher: String!
    pubDate: String
    pageNum: Int
  }

  type Person {
    guid: String
    names: [String]
  }

  type Query {

    # this allows us to populate the map with summaries of other visible places
    getPlaceSummaryByTimeTag(
      boundingBox: BoundingBox,
      timeTagGUID: String
    ): [PlaceSummaryByTimeTag]

    getEventFeed(
      direction: Direction,
      mode: FocusType,
      currentFocusGUID: String          # depending on mode, this needs to be a person guid, place guid, or time guid
    ): TimeTagByFocus

    getTimeTagSummary(
      mode: FocusType,
      focusGUID: String
    ): [TimeTagSummary]
  }

  enum Direction {
    # Which direction in time are we headed?
    FUTURE
    PAST
  }

  enum FocusType {
    TIME
    PERSON
    PLACE
  }

`

/*


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