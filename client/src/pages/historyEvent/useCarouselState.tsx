import { useState, useCallback, useRef } from "react";
import { HistoryEvent } from "../../graphql/events";

export const useCarouselState = (
  initialEvents: HistoryEvent[],
  initialIndex: number
) => {
  const [historyEvents, setHistoryEvents] = useState(initialEvents);
  const [currentEventIndex, setCurrentEventIndex] = useState(initialIndex);

  const isLoadingRef = useRef(false);

  const loadMoreEvents = useCallback(
    async (
      direction: "left" | "right",
      loadFn: () => Promise<HistoryEvent[]>
    ) => {
      if (isLoadingRef.current) return; // Prevent re-entry if already loading
      isLoadingRef.current = true;

      const newEvents = await loadFn();
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
    [isLoadingRef]
  );

  return {
    historyEvents,
    currentEventIndex,
    setCurrentEventIndex,
    loadMoreEvents,
  };
};
