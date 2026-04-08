import { useState, useCallback, useEffect, useRef } from "react";
import { HistoryEvent } from "../../graphql/events";

export const useCarouselState = (
  initialEvents: HistoryEvent[],
  initialIndex: number,
) => {
  const [historyEvents, setHistoryEvents] = useState(initialEvents);
  const [currentEventIndex, setCurrentEventIndex] = useState(initialIndex);

  const isLoadingRef = useRef(false);

  // React to changes in initialEvents and initialIndex
  useEffect(() => {
    setHistoryEvents(initialEvents);
    setCurrentEventIndex(initialIndex);
  }, [initialEvents, initialIndex]);

  const loadMoreEvents = useCallback(
    async (
      direction: "left" | "right",
      loadFn: (eventId: string) => Promise<HistoryEvent[]>,
    ) => {
      if (isLoadingRef.current) return; // Prevent re-entry if already loading
      isLoadingRef.current = true;

      const newEvents = await loadFn(historyEvents[currentEventIndex].id);
      if (direction === "left") {
        setCurrentEventIndex((prevIndex) => prevIndex + newEvents.length);
      }
      setHistoryEvents((prevEvents) => {
        if (direction === "left") {
          return [...newEvents, ...prevEvents];
        } else {
          return [...prevEvents, ...newEvents];
        }
      });

      isLoadingRef.current = false;
    },
    [currentEventIndex, historyEvents],
  );

  return {
    historyEvents,
    currentEventIndex,
    setCurrentEventIndex,
    loadMoreEvents,
  };
};
