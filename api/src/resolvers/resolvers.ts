/*

*/
import { Context } from '../index';
import {
  PlaceSummaryByTimeTag,
  TimeTagByFocus,
  Point,
  Location,
  BoundingBox,
  Citation,
  Tag,
  MetaData,
  Person
} from '../types'


type ResolverFn = (parent: any, args: any, ctx: any) => any;
interface ResolverMap {
  [field: string]: ResolverFn;
}
interface Resolvers {
  Query: ResolverMap;
  TimeTagByFocus: ResolverMap;
  PlaceSummaryByTimeTag: ResolverMap;
  Location: ResolverMap;
  Point: ResolverMap;
  BoundingBox: ResolverMap;
  Citation: ResolverMap;
  Tag: ResolverMap;
  MetaData: ResolverMap;
}

export const resolvers: Resolvers = {
  Query: {

    getPlaceSummaryByTimeTag: (root, args: {
      boundingBox: BoundingBox,
      timeTagGUID: string
    }, ctx: Context) => {
      return [placeSummary];
    },

    getEventFeed: (root, args: { 
      direction: "FUTURE" | "PAST",
      mode: "TIME" | "PERSON" | "PLACE",
      currentFocusGUID: string
     }, ctx: Context) => {

    },

    getTimeTagSummary: (root, args: {
      mode: "TIME" | "PERSON" | "PLACE",
      focusGUID: string
    }, ctx: Context) => {

    }

  },


  TimeTagByFocus: {

    citations: (ttbf: TimeTagByFocus, args, ctx) => {

    },

    adjacentPeople: (ttbf: TimeTagByFocus, args, ctx) => {
      
    }

  },

  PlaceSummaryByTimeTag: {

  },
  Location: {
    
  },
  Point: {

  },
  BoundingBox: {

  },
  Citation: {

  },
  Tag: {

  },
  MetaData: {

  }

}


const placeSummary: PlaceSummaryByTimeTag = {
  placeName: ['Rome', 'Roma'],
  placeLocation: {
    point: {
      latitude: 100,
      longitude: 100
    }
  },
  citationCount: 35,
  personCount: 12
}

