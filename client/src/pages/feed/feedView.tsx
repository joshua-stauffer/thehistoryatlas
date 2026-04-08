import React, { useCallback, useEffect, useRef, useState } from "react";
import { useLoaderData } from "react-router-dom";
import {
  Box,
  CircularProgress,
  Container,
  Typography,
} from "@mui/material";
import { FeedPageData } from "./feedLoader";
import { FeedEvent, fetchFeed } from "../../api/feed";
import { ThemeFilter } from "./themeFilter";
import { FeedCard } from "./feedCard";

export const FeedView: React.FC = () => {
  const { feed: initialFeed, categories } =
    useLoaderData() as FeedPageData;

  const [events, setEvents] = useState<FeedEvent[]>(initialFeed.events);
  const [cursor, setCursor] = useState<string | null>(
    initialFeed.nextCursor,
  );
  const [selectedThemes, setSelectedThemes] = useState<Set<string>>(
    new Set(),
  );
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Reload feed when theme filters change
  useEffect(() => {
    let cancelled = false;
    const loadFeed = async () => {
      setLoading(true);
      try {
        const result = await fetchFeed({
          themes:
            selectedThemes.size > 0
              ? Array.from(selectedThemes)
              : undefined,
        });
        if (!cancelled) {
          setEvents(result.events);
          setCursor(result.nextCursor);
        }
      } catch {
        // ignore errors on cancelled requests
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadFeed();
    return () => {
      cancelled = true;
    };
  }, [selectedThemes]);

  // Infinite scroll via IntersectionObserver
  const loadMore = useCallback(async () => {
    if (!cursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const result = await fetchFeed({
        themes:
          selectedThemes.size > 0
            ? Array.from(selectedThemes)
            : undefined,
        afterCursor: cursor,
      });
      setEvents((prev) => [...prev, ...result.events]);
      setCursor(result.nextCursor);
    } catch {
      // ignore
    } finally {
      setLoadingMore(false);
    }
  }, [cursor, loadingMore, selectedThemes]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadMore]);

  const handleToggleTheme = (slug: string) => {
    setSelectedThemes((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      return next;
    });
  };

  return (
    <Box sx={{ backgroundColor: "background.default", minHeight: "100vh" }}>
      <Container maxWidth="sm" sx={{ pt: { xs: 2, sm: 3 }, pb: 4 }}>
        <Typography variant="h1" sx={{ fontSize: { xs: "1.75rem", sm: "2.5rem" } }}>
          The History Atlas
        </Typography>

        <ThemeFilter
          categories={categories}
          selectedSlugs={selectedThemes}
          onToggle={handleToggleTheme}
        />

        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
            <CircularProgress />
          </Box>
        ) : events.length === 0 ? (
          <Typography
            variant="body1"
            sx={{ textAlign: "center", mt: 4, color: "text.secondary" }}
          >
            No events found. Try adjusting your filters.
          </Typography>
        ) : (
          <>
            {events.map((event) => (
              <FeedCard key={event.summaryId} event={event} />
            ))}

            <div ref={sentinelRef} />

            {loadingMore && (
              <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
                <CircularProgress size={28} />
              </Box>
            )}

            {!cursor && events.length > 0 && (
              <Typography
                variant="body2"
                sx={{ textAlign: "center", py: 2, color: "text.secondary" }}
              >
                You've reached the end.
              </Typography>
            )}
          </>
        )}
      </Container>
    </Box>
  );
};
