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
  CardContent,
  CardHeader,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { renderDateTime } from "../../components/renderDateTime/time";
import { useState } from "react";
import { TimeTravelModal } from "./timeTravelModal";
import { StoryCard } from "./storyCard";
import Autocomplete from "@mui/material/Autocomplete";

interface NewFeedProps {
  event: EventItem;
  next: () => void;
  prev: () => void;
}

export const NewFeed = (props: NewFeedProps) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const handleOpen = () => setIsOpen(true);
  const handleClose = () => setIsOpen(false);

  const coords = props.event.map.locations.map((location) => {
    return {
      latitude: location.latitude,
      longitude: location.longitude,
    };
  });
  return (
    <Box>
      <TimeTravelModal isOpen={isOpen} handleClose={handleClose} />
      <Grid container spacing={5} direction={"row"} justifyItems={"center"}>
        {/* Event Feed */}

        <Grid item sm={12} md={6}>
          {/* left box desktop, top box mobile */}

          <NewFeedCard event={props.event} openTimeTravelModal={handleOpen} />
          <StoryCard event={props.event} />

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
          <Card sx={{ height: "100px" }}>
            <CardContent>
              <Typography
                variant={"h1"}
                sx={{ textAlign: "center", fontSize: "20px" }}
              >
                The History Atlas
              </Typography>
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
        </Grid>
      </Grid>
    </Box>
  );
};
