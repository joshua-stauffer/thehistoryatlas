export interface EventItem {
  id: string;
  text: string;
  lang: string;
  date: CalendarDate;
  source: Source; // todo: make list
  tags: Tag[];
  map: Map;
  focus: Focus | null;
  story: Story;
  relatedStories: Story[];
}

export interface CalendarDate {
  time: string;
  calendar: string;
  precision: number;
}

export interface Source {
  id: string;
  text: string;
  title: string;
  author: string;
  publisher: string;
  pubDate: string;
}

export type Tag = Person | Place | Time;

export interface Person {
  id: string;
  type: "PERSON";
  startChar: number;
  stopChar: number;
  name: string;
}
export interface Place {
  id: string;
  type: "PLACE";
  startChar: number;
  stopChar: number;
  name: string;
  location: Location;
}
export interface Time {
  id: string;
  type: "TIME";
  startChar: number;
  stopChar: number;
  name: string;
  time: string;
  calendar: string;
  precision: number;
}

export interface Map {
  locations: Location[];
}

type Location = Point;

export interface Point {
  id: string;
  longitude: number;
  latitude: number;
  name: string;
}

export interface Shape {
  id: string;
  name: string;
  geoShape: string;
}

export interface Focus {
  id: string;
  type: FocusType;
  name: string;
}

type FocusType = "PERSON" | "PLACE";

export interface PeopleAndPlaceOption {
  name: string;
  id: string;
  type: "PERSON" | "PLACE";
}

export interface Story {
  id: string;
  name: string;
}
