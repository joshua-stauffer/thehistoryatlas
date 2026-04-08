import { API_BASE_URL } from "../config";

export interface Theme {
  id: string;
  name: string;
  slug: string;
}

export interface ThemeCategory {
  id: string;
  name: string;
  slug: string;
  children: Theme[];
}

export interface ThemesResponse {
  categories: ThemeCategory[];
}

export const fetchThemes = async (): Promise<ThemesResponse> => {
  const response = await fetch(`${API_BASE_URL}/themes`);
  if (!response.ok) {
    throw new Error("Failed to fetch themes");
  }
  return response.json();
};
