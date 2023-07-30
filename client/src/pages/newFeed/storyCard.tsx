import { Button, Card, CardActions, CardHeader } from "@mui/material";
import { EventItem } from "../../graphql/events";

interface StoryCardProps {
  event: EventItem;
}
export const StoryCard = (props: StoryCardProps) => {
  return (
    <Card sx={{ height: "25%", marginTop: 3 }}>
      <CardHeader
        title={"Stories"}
        subheader={"Stories in which this event appears"}
        sx={{ textAlign: "center" }}
      />
      <CardActions>
        <Button disabled>{props.event.story.name} (current Story)</Button>
        <br />
        {props.event.relatedStories.map((story) => (
          <>
            <Button>{story.name}</Button>
            <br />
          </>
        ))}
      </CardActions>
    </Card>
  );
};
