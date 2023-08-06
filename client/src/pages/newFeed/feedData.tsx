import { NewFeed } from "./newFeed";
import { events } from "../../data";
import { useParams } from "react-router-dom";

export const FeedData = () => {
  const { storyId, eventId } = useParams();
  return <NewFeed event={events[0]} next={() => null} prev={() => null} />;
};
