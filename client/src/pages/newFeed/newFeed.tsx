import Box from "@mui/material/Box";
import {
  AddCitationButton,
  LoginButton,
  NavBar,
  SettingsButton,
} from "../../components/navBar";
import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import { TagBox } from "../feed/tagBox";
import Hidden from "@mui/material/Hidden";
import { SingleEntityMap } from "../../components/singleEntityMap";
import { EventItem } from "../../graphql/events";
import { NewFeedCard } from "./newFeedCard";
import { FilterTags } from "./filterTags";
import {
  Button,
  Card,
  CardActions,
  CardHeader,
  Stack,
  Typography,
} from "@mui/material";
import { renderDateTime } from "../../components/renderDateTime/time";

interface NewFeedProps {
  event: EventItem;
  next: () => void;
  prev: () => void;
}

export const NewFeed = (props: NewFeedProps) => {
  const coords = props.event.map.locations.map((location) => {
    return {
      latitude: location.latitude,
      longitude: location.longitude,
    };
  });
  return (
    <Box>
      <NavBar children={[<AddCitationButton />, <SettingsButton />]} />
      <Box sx={{ height: 70 }}></Box>
      <Grid container spacing={5} direction={"row"} justifyItems={"center"}>
        {/* Event Feed */}

        <Grid item sm={12} md={6}>
          {/* left box desktop, top box mobile */}

          <NewFeedCard event={props.event} />

          <Hidden mdUp>
            {/* Inline map for mobile */}
            <SingleEntityMap
              coords={coords}
              mapTyle={"natGeoWorld"}
              size={"SM"}
              title={props.event.map.locations[0].name}
              zoom={6}
            />
          </Hidden>
        </Grid>
        <Grid item md={6}>
          {/* right box desktop, bottom box mobile */}
          <Hidden smDown>
            {/* Standalone map for desktop */}
            <SingleEntityMap
              coords={coords}
              mapTyle={"natGeoWorld"}
              size={"MD"}
              title={props.event.map.locations[0].name}
              zoom={7}
            />
          </Hidden>
          <Card>
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

              <Button>The History of Everything</Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
