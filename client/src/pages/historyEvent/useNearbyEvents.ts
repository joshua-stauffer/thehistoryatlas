import { useState, useEffect, useRef, useCallback } from "react";
import { NearbyEvent, fetchNearbyEvents } from "../../api/nearbyEvents";
import { HistoryEvent } from "../../graphql/events";

export interface MapBounds {
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
}

export const useNearbyEvents = (currentEvent: HistoryEvent | undefined) => {
  const [nearbyEvents, setNearbyEvents] = useState<NearbyEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastEventIdRef = useRef<string | null>(null);

  // Clear events when event changes
  useEffect(() => {
    if (currentEvent?.id !== lastEventIdRef.current) {
      lastEventIdRef.current = currentEvent?.id ?? null;
      setNearbyEvents([]);

      // Cancel any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    }
  }, [currentEvent?.id]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const loadNearbyEvents = useCallback(
    (bounds: MapBounds) => {
      if (!currentEvent) return;

      // Clear previous debounce timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(async () => {
        // Cancel previous in-flight request
        if (abortControllerRef.current) {
          abortControllerRef.current.abort();
        }

        const controller = new AbortController();
        abortControllerRef.current = controller;

        setIsLoading(true);
        try {
          const response = await fetchNearbyEvents(
            {
              eventId: currentEvent.id,
              calendarModel: currentEvent.date.calendar,
              precision: currentEvent.date.precision,
              datetime: currentEvent.date.datetime,
              minLat: bounds.minLat,
              maxLat: bounds.maxLat,
              minLng: bounds.minLng,
              maxLng: bounds.maxLng,
            },
            controller.signal,
          );
          // Only update if this request wasn't cancelled
          if (!controller.signal.aborted) {
            setNearbyEvents(response.events);
          }
        } catch (error) {
          if (error instanceof Error && error.name !== "AbortError") {
            console.error("Failed to fetch nearby events:", error);
          }
        } finally {
          if (!controller.signal.aborted) {
            setIsLoading(false);
          }
        }
      }, 300);
    },
    [currentEvent],
  );

  return { nearbyEvents, isLoading, loadNearbyEvents };
};
