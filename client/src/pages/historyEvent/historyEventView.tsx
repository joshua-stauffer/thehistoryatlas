import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Hidden from "@mui/material/Hidden";
import { SingleEntityMap } from "../../components/singleEntityMap";
import React, { useCallback, useEffect, useState } from "react";
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
import Autocomplete from "@mui/material/Autocomplete";
import { sansSerifFont } from "../../baseStyle";
import SearchIcon from "@mui/icons-material/Search";
import Divider from "@mui/material/Divider";
import { EventPointer, HistoryEvent } from "../../graphql/events";
import EmblaCarousel from "./carousel";

const buildSlides = (events: HistoryEvent[]): JSX.Element[] => {
  return events.map((historyEvent, index) => (
    <EventView event={historyEvent} key={index} />
  ));
};

export const HistoryEventView = () => {
  const { events, index, loadNext, loadPrev } =
    useLoaderData() as HistoryEventData;

  const [carouselState, setCarouselState] = useState({
    historyEvents: events,
    currentEventIndex: index,
    slides: buildSlides(events),
  });

  const setFocusedIndex = (index: number) => {
    setCarouselState((prevState) => {
      return { ...prevState, currentEventIndex: index };
    });
  };

  const navigate = useNavigate();

  if (carouselState.historyEvents.length <= 0) throw new Error("No data");

  const currentEvent =
    carouselState.historyEvents[carouselState.currentEventIndex];

  const coords = currentEvent.map.locations.map((location) => {
    return {
      latitude: location.latitude,
      longitude: location.longitude,
    };
  });
  const loadLeft = () => {
    setCarouselState((prevState) => {
      const newSlides = loadPrev();
      return {
        historyEvents: [...newSlides, ...prevState.historyEvents],
        currentEventIndex: prevState.currentEventIndex + newSlides.length,
        slides: buildSlides([...newSlides, ...prevState.historyEvents]),
      };
    });
  };

  const loadRight = () => {
    setCarouselState((prevState) => {
      const newSlides = loadNext();
      return {
        historyEvents: [...prevState.historyEvents, ...newSlides],
        currentEventIndex: prevState.currentEventIndex - newSlides.length,
        slides: buildSlides([...prevState.historyEvents, ...newSlides]),
      };
    });
  };

  return (
    <Box sx={{ height: "92vh", maxHeight: "1000px" }}>
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
              {currentEvent.storyTitle}
            </Typography>
            <Divider
              sx={{
                marginTop: "10px",
                marginBottom: "10px",
              }}
            />
            <EmblaCarousel
              slides={carouselState.slides}
              setFocusedIndex={setFocusedIndex}
              startIndex={index}
              loadNext={loadRight}
              loadPrev={loadLeft}
            />

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
