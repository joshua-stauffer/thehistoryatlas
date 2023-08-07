import { HistoryEvent } from "./historyEvent";
import { events } from "../../data";
import { useParams } from "react-router-dom";

export const FeedData = () => {
  const { storyId, eventId } = useParams();
  return <HistoryEvent event={events[0]} next={() => null} prev={() => null} />;
};
