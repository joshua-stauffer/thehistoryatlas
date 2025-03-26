import { debounce } from 'lodash';

export interface StorySearchResult {
  name: string;
  id: string;
}

export interface StorySearchResponse {
  results: StorySearchResult[];
}

const searchStories = async (query: string): Promise<StorySearchResponse> => {
  const response = await fetch(`http://localhost:8000/api/stories/search?query=${encodeURIComponent(query)}`);
  if (!response.ok) {
    throw new Error('Failed to search stories');
  }
  return response.json();
};

// Debounced version that limits to 2 requests per second (500ms delay)
export const debouncedSearchStories = debounce(searchStories, 500); 