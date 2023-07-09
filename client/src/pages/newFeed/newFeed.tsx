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
import { NewTagBox } from "./newTagBox";

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
    <Box sx={{ flexGrow: 1 }}>
      <NavBar children={[<AddCitationButton />, <SettingsButton />]} />
      <Box sx={{ height: 70 }}></Box>
      <Grid container spacing={10} direction={"row"} justifyItems={"center"}>
        {/* Event Feed */}
        <Grid
          item
          sm={12}
          md={6}
          sx={{
            maxHeight: "100vh",
            overflow: "scroll",
          }}
        >
          <Paper sx={{ marginTop: "55px" }}>
            <Grid item id={`event-card-x`} xs={12} md={12}>
              <Paper>
                <NewFeedCard event={props.event} />
              </Paper>
            </Grid>
            <Grid item xs={12} md={12} id={`event-tags-x`}>
              <NewTagBox tags={props.event.tags} />
            </Grid>
            <Hidden mdUp>
              {/* Inline map for mobile */}
              <Grid item sm={12}>
                <SingleEntityMap
                  coords={coords}
                  mapTyle={"natGeoWorld"}
                  size={"SM"}
                  title={props.event.map.locations[0].name}
                  zoom={6}
                />
              </Grid>
            </Hidden>
          </Paper>
          <Grid
            item
            sx={{
              height: "70vh",
            }}
          >
            {/* Spacer for the end of the feed */}
          </Grid>
        </Grid>
        <Hidden smDown>
          {/* Standalone map for desktop */}
          <Grid item md={6}>
            <SingleEntityMap
              coords={coords}
              mapTyle={"natGeoWorld"}
              size={"MD"}
              title={props.event.map.locations[0].name}
              zoom={6}
            />
          </Grid>
        </Hidden>
      </Grid>
    </Box>
  );
};
