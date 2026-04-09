import { API_BASE_URL } from "../config";

export interface FeedTag {
  id: string;
  type: string;
  name: string;
}

export interface FeedTheme {
  slug: string;
  name: string;
}

export interface FeedEvent {
  summaryId: string;
  summaryText: string;
  tags: FeedTag[];
  themes: FeedTheme[];
  latitude: number | null;
  longitude: number | null;
  datetime: string | null;
  precision: number | null;
  isFavorited: boolean;
}

export interface FeedResponse {
  events: FeedEvent[];
  nextCursor: string | null;
}

export const fetchFeed = async (
  params: {
    themes?: string[];
    afterCursor?: string;
    limit?: number;
  } = {},
  signal?: AbortSignal,
): Promise<FeedResponse> => {
  const queryParams = new URLSearchParams();
  if (params.themes) {
    params.themes.forEach((t) => queryParams.append("themes", t));
  }
  if (params.afterCursor) {
    queryParams.append("afterCursor", params.afterCursor);
  }
  if (params.limit) {
    queryParams.append("limit", params.limit.toString());
  }
  const response = await fetch(
    `${API_BASE_URL}/feed?${queryParams.toString()}`,
    { signal },
  );
  if (!response.ok) {
    throw new Error("Failed to fetch feed");
  }
  return response.json();
};
