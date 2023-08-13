import {
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  TextField,
} from "@mui/material";
import { HistoryEvent } from "../../graphql/events";
import Autocomplete from "@mui/material/Autocomplete";
import { sansSerifFont, serifFont } from "../../baseStyle";
import { Link } from "react-router-dom";

interface StoryCardProps {
  event: HistoryEvent;
}
export const StoryCard = (props: StoryCardProps) => {
  const buttonSX = {
    textTransform: "none",
  };
  return (
    <Card sx={{ marginTop: 3, minHeight: "30vh", maxHeight: "500px" }}>
      <CardHeader
        title={"Stories"}
        subheaderTypographyProps={{ fontFamily: sansSerifFont }}
        subheader={"Other stories in which include this event"}
        sx={{ textAlign: "center", fontFamily: sansSerifFont }}
      />
      <CardActions>
        {props.event.relatedStories.map((story) => (
          <>
            <Link to={`/stories/${story.id}/events/${props.event.id}`}>
              <Button sx={{ ...buttonSX, fontFamily: serifFont }}>
                {story.name}
              </Button>
            </Link>
            <br />
          </>
        ))}
      </CardActions>
      <CardContent></CardContent>
    </Card>
  );
};
