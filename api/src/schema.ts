

const { gql } = require('apollo-server')

export const typeDefs = gql`
  type Query {

    GetCitationsByGUID(
      citationGUIDs: [String!]!
    ): [Citation]

    GetManifest(
      entityType: EntityType!
      GUID: String!
    ): Manifest!

    GetGUIDsByName(
      name: String!
    ): GUIDs!
  }

  type Mutation {

    PublishNewCitation(
      AnnotatedCitation: AnnotateCitationInput!
    ): PublishCitationResponse!

  }

  # general types
  
  type CitationByGUID {
    citation_guid: String
  }

  type Citation {
    guid: String!
    text: String!
    tags: [Tag!]!
    meta: MetaData!
  }

  type Manifest {
    guid: String!
    citation_guids: [String]
  }

  type GUIDs {
    guids: [String]
  }

  type Tag {
    tag_type: EntityType!
    tag_guid: String!     # which entity does this tag refer to?
    start_char: Int!      # index of character in text 
    stop_char: Int!       # index of character in text 
    name: String
    names: [String]
    coords: Geo
  }

  type MetaData {
    title: String!
    author: String!
    publisher: String!
    pubDate: String
    pageNum: Int
  }

  enum EntityType {
    TIME
    PERSON
    PLACE
  }

  # geo types

  type Point {
    latitude: Float!
    longitude: Float!
  }

  type BoundingBox {
    upperLeft: Point
    lowerRight: Point
  }

  type Geo {
    point: Point!
    shape: [ Point ]
  }

  # mutation types

  input AnnotateCitationInput {
    text: String!
    tags: [TagInput!]!
    meta: MetaDataInput!
  }

  input TagInput {
    type: EntityType!
    start_char: Int!
    stop_char: Int!
    GUID: String!
    name: String!
    latitude: Float
    longitude: Float
    geoshape: String
  }

  input MetaDataInput {
    title: String!
    author: String!
    publisher: String!
    pubDate: String
    pageNum: Int
    GUID: String!
  }

  interface MutationResponse {
    code: String!
    success: Boolean!
    message: String!
  }

  type PublishCitationResponse implements MutationResponse {
    code: String!
    success: Boolean!
    message: String!
  }
`

/*
`

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