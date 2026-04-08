import { fetchFeed, FeedResponse } from "../../api/feed";
import { fetchThemes, ThemeCategory } from "../../api/themes";

export interface FeedPageData {
  feed: FeedResponse;
  categories: ThemeCategory[];
}

export const feedLoader = async (): Promise<FeedPageData> => {
  const [feed, themes] = await Promise.all([fetchFeed(), fetchThemes()]);
  return {
    feed,
    categories: themes.categories,
  };
};
