

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
