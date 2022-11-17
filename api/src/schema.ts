// const { gql } = require("apollo-server");
const { gql } = require("graphql-tag");
// import { gql } from 'graphql-tag';

export const typeDefs = gql`
  extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key", "@shareable"])
  
  type Query {
    GetSummariesByGUID(summary_guids: [String!]!): [Summary]

    GetEntitySummariesByGUID(guids: [String!]!): [EntitySummary]!

    GetCitationByGUID(citationGUID: String!): Citation

    GetManifest(entityType: EntityType!, GUID: String!): Manifest!

    GetGUIDsByName(name: String!): GUIDSummaries!

    GetCoordinatesByName(name: String!): [GeoResponse]

    GetFuzzySearchByName(name: String!): [FuzzySearchResponse]

    GetTextAnalysis(text: String!): TextAnalysisResponse

    IsUsernameUnique(username: String!): IsUsernameUniqueResponse!

    GetUser(token: String!): AccountsGenericResponse!

    GetPlaceByCoords(latitude: Float!, longitude: Float!): PlaceByCoordsResponse!
  }

  type Mutation {
    PublishNewCitation(
      Annotation: AnnotateCitationInput!
    ): PublishCitationResponse!

    ConfirmAccount(token: String!): AccountsGenericResponse!

    DeactivateAccount(
      token: String!
      username: String!
    ): AccountsGenericResponse

    UpdateUser(
      token: String!
      user_details: UpdateUserDetailsInput!
      credentials: CredentialsInput
    ): AccountsGenericResponse!

    AddUser(
      token: String!
      user_details: NewUserDetailsInput!
    ): AccountsGenericResponse!

    Login(username: String!, password: String!): LoginResponse!
  }

  # general types

  type Summary {
    guid: String!
    text: String!
    tags: [Tag!]!
    citation_guids: [String!]!
  }

  type CitationByGUID {
    citation_guid: String
  }

  type Citation {
    guid: String!
    text: String!
    # tags: [Tag!]!
    meta: MetaData!
  }

  type Manifest {
    guid: String!
    citation_guids: [String]
    timeline: [Timeline]!
  }

  type Timeline {
    year: Int!
    count: Int!
    root_guid: String!
  }

  type GUIDSummaries {
    guids: [String]
    summaries: [GUIDSummary]
  }

  type GUIDSummary {
    type: String
    guid: String
    citation_count: Int
    names: [String]
    first_citation_date: String
    last_citation_date: String
  }

  type EntitySummary {
    type: EntityType!
    guid: String!
    citation_count: Int!
    names: [String!]!
    first_citation_date: String!
    last_citation_date: String!
  }

  type Tag {
    tag_type: EntityType!
    tag_guid: String! # which entity does this tag refer to?
    start_char: Int! # index of character in text
    stop_char: Int! # index of character in text
    name: String
    names: [String]
    coords: Coords
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

  type TextAnalysisResponse {
    text: String
    text_map: TextMap
    boundaries: [TextBoundaries]
  }

  type TextAnalysis {
    text: String
    start_char: Int
    stop_char: Int
    guids: [String]
    coords: [GeoResponse]
  }

  type TextMap {
    PERSON: [TextAnalysis]
    PLACE: [TextAnalysis]
    TIME: [TextAnalysis]
  }

  type TextBoundaries {
    text: String
    start_char: Int
    stop_char: Int
  }

  type FuzzySearchResponse {
    name: String!
    guids: [String]!
  }

  # geo types
  type Coords {
    latitude: Float
    longitude: Float
    geoshape: String
  }

  type GeoResponse {
    longitude: Float
    latitude: Float
    geoshape: String
  }

  type PlaceByCoordsResponse {
    latitude: Float!
    longitude: Float!
    guid: String
  }

  # mutation types

  input AnnotateCitationInput {
    citation_guid: String!
    citation: String!
    summary_guid: String!
    summary: String!
    summary_tags: [TagInput!]!
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

  # Accounts Service Types

  type AccountsGenericResponse {
    token: String!
    user_details: UserDetails!
  }

  type UserDetails {
    f_name: String!
    l_name: String!
    username: String!
    email: String!
    last_login: String!
  }

  input CredentialsInput {
    username: String!
    password: String!
  }

  input NewUserDetailsInput {
    f_name: String!
    l_name: String!
    username: String!
    password: String!
    email: String!
  }

  input UpdateUserDetailsInput {
    f_name: String
    l_name: String
    username: String
    password: String
    email: String
  }

  type IsUsernameUniqueResponse {
    username: String!
    is_unique: Boolean!
  }

  type LoginResponse {
    success: Boolean!
    token: String
  }
`;
