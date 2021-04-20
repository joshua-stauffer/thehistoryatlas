

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
    ): [Citation]

    SearchFocusByName(
      focusType: FocusType!
      searchTerm: String!
    ): [Focus]

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

  type Focus {
    names: [String!]!
    GUID: String!
  }

  enum FocusType {
    TIME
    PERSON
    PLACE
  }

  type Mutation {
    AddAnnotatedCitation(annotatedCitation: AnnotateCitation): AnnotateCitationResponse
  }

  input AnnotateCitation {
    "The citation text"
    text: String!
    "Tags of who, where, and when"
    tags: [TagInput!]!
    "Source information"
    meta: MetaDataInput!
  }

  input TagInput {
    type: FocusType!
    start: Int!
    end: Int!
    GUID: String!
  }

  input MetaDataInput {
    author: String!
    publisher: String!
    pubDate: String
    pageNum: Int
  }

  interface MutationResponse {
    code: String!
    success: Boolean!
    message: String!
  }

  type AnnotateCitationResponse implements MutationResponse {
    code: String!
    success: Boolean!
    message: String!
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