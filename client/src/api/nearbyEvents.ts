import { API_BASE_URL } from "../config";

export interface NearbyEvent {
  eventId: string;
  storyId: string;
  personName: string;
  personDescription: string | null;
  summaryText: string | null;
  placeName: string;
  latitude: number;
  longitude: number;
  datetime: string;
  precision: number;
  calendarModel: string;
}

export interface NearbyEventsResponse {
  events: NearbyEvent[];
}

export interface NearbyEventsParams {
  eventId: string;
  calendarModel: string;
  precision: number;
  datetime: string;
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
}

export const fetchNearbyEvents = async (
  params: NearbyEventsParams,
  signal?: AbortSignal,
): Promise<NearbyEventsResponse> => {
  const queryParams = new URLSearchParams({
    eventId: params.eventId,
    calendarModel: params.calendarModel,
    precision: String(params.precision),
    datetime: params.datetime,
    minLat: String(params.minLat),
    maxLat: String(params.maxLat),
    minLng: String(params.minLng),
    maxLng: String(params.maxLng),
  });

  const response = await fetch(
    `${API_BASE_URL}/history/nearby?${queryParams.toString()}`,
    { signal },
  );
  if (!response.ok) {
    throw new Error("Failed to fetch nearby events");
  }
  return response.json();
};
