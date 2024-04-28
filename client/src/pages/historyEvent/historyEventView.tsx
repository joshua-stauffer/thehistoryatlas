import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Hidden from "@mui/material/Hidden";
import { SingleEntityMap } from "../../components/singleEntityMap";

import React, { useState } from "react";
import { TimeTravelModal } from "./timeTravelModal";
import { Link, useLoaderData, useNavigate } from "react-router-dom";
import { HistoryEventData } from "./historyEventLoader";
import {
  Button,
  ButtonGroup,
  InputAdornment,
  SpeedDial,
  SpeedDialIcon,
  TextField,
  Typography,
} from "@mui/material";
import { EventView } from "./eventView";
import SwipeableViews from "react-swipeable-views";
import { bindKeyboard } from "react-swipeable-views-utils";
import Autocomplete from "@mui/material/Autocomplete";
import { sansSerifFont } from "../../baseStyle";
import SearchIcon from "@mui/icons-material/Search";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import Divider from "@mui/material/Divider";
import { EventPointer } from "../../graphql/events";
import EmblaCarousel from "./carousel";

const BindKeyboardSwipeableViews = bindKeyboard(SwipeableViews);

export const HistoryEventView = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const handleOpen = () => setIsOpen(true);
  const handleClose = () => setIsOpen(false);
  const navigate = useNavigate();

  const { events, story, index, currentEvent, prevEvent, nextEvent } =
    useLoaderData() as HistoryEventData;
  const coords = currentEvent.map.locations.map((location) => {
    return {
      latitude: location.latitude,
      longitude: location.longitude,
    };
  });
  const data = useLoaderData();
  console.log({ data });

  const SLIDES = events.map((historyEvent, index) => (
    <EventView event={historyEvent} />
  ));

  return (
    <Box sx={{ height: "92vh", maxHeight: "1000px" }}>
      <TimeTravelModal isOpen={isOpen} handleClose={handleClose} />
      <Grid container spacing={5} direction={"row"} justifyItems={"center"}>
        {/* Event Feed */}

        <Grid item sm={12} md={6}>
          {/* left box desktop, top box mobile */}
          <Box
            sx={{
              marginTop: "auto",
              marginBottom: "auto",
              paddingTop: "1vh",
              minHeight: "92vh",
              maxHeight: "1200px",
              padding: "20px",
            }}
          >
            <Autocomplete
              sx={{ fontFamily: sansSerifFont }}
              id="story-search"
              freeSolo
              options={currentEvent.tags.map((tag) => tag.name)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Search for a story"
                  variant={"outlined"}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              )}
            />
            <Typography
              variant={"h1"}
              sx={{
                textAlign: "center",
                marginTop: "5vh",
                marginBottom: "2vh",
              }}
            >
              {story.name}
            </Typography>
            <Divider
              sx={{
                marginTop: "10px",
                marginBottom: "10px",
              }}
            />
            <EmblaCarousel slides={SLIDES} />

            <Hidden mdUp>
              {/* Inline map for mobile */}
              <SingleEntityMap
                coords={coords}
                mapTyle={"natGeoWorld"}
                size={"SM"}
                title={currentEvent.map.locations[0].name}
                zoom={6}
              />
            </Hidden>
          </Box>
        </Grid>

        <Grid item md={6}>
          {/* right box desktop, bottom box mobile */}
          <Hidden smDown>
            {/* Standalone map for desktop */}
            <SingleEntityMap
              coords={coords}
              mapTyle={"natGeoWorld"}
              size={"MD"}
              title={currentEvent.map.locations[0].name}
              zoom={7}
            />
          </Hidden>
        </Grid>
      </Grid>
      <SpeedDial
        ariaLabel="Add new Event"
        sx={{ position: "absolute", top: 16, right: 16 }}
        icon={<SpeedDialIcon />}
        onClick={() => navigate("/add-event")}
      ></SpeedDial>
    </Box>
  );
};

const buildUrlFor = (pointer: EventPointer) => {
  return `/stories/${pointer.storyId}/events/${pointer.id}`;
};
