import {
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  TextField,
} from "@mui/material";
import { EventItem } from "../../graphql/events";
import Autocomplete from "@mui/material/Autocomplete";

interface StoryCardProps {
  event: EventItem;
}
export const StoryCard = (props: StoryCardProps) => {
  return (
    <Card sx={{ marginTop: 3 }}>
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
      <CardContent>
        <Autocomplete
          id="story-search"
          freeSolo
          options={props.event.tags.map((tag) => tag.name)}
          renderInput={(params) => (
            <TextField {...params} label="Search for a story" />
          )}
        />
      </CardContent>
    </Card>
  );
};
