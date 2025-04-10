import { API_BASE_URL } from '../config';

export interface StorySearchResult {
  name: string;
  id: string;
}

export interface StorySearchResponse {
  results: StorySearchResult[];
}

const searchStories = async (query: string): Promise<StorySearchResponse> => {
  const response = await fetch(
    `${API_BASE_URL}/stories/search?query=${encodeURIComponent(query)}`,
  );
  if (!response.ok) {
    throw new Error("Failed to search stories");
  }
  return response.json();
};

export const debouncedSearchStories = searchStories;
