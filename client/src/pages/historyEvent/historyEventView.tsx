import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Hidden from "@mui/material/Hidden";
import { SingleEntityMap } from "../../components/singleEntityMap";
import React, { useState } from "react";
import { useLoaderData, useNavigate } from "react-router-dom";
import { HistoryEventData } from "./historyEventLoader";
import { InputAdornment, TextField, Typography } from "@mui/material";
import { EventView } from "./eventView";
import Autocomplete from "@mui/material/Autocomplete";
import { sansSerifFont } from "../../baseStyle";
import SearchIcon from "@mui/icons-material/Search";
import Divider from "@mui/material/Divider";
import { EventPointer } from "../../graphql/events";
import EmblaCarousel from "./carousel";
import { useCarouselState } from "./useCarouselState";
import { StorySearchResult } from "../../api/stories";
import { debouncedSearchStories } from "../../api/stories";

export const HistoryEventView = () => {
  const { events, index, loadNext, loadPrev } =
    useLoaderData() as HistoryEventData;
  const [searchResults, setSearchResults] = useState<StorySearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const {
    historyEvents,
    currentEventIndex,
    setCurrentEventIndex,
    loadMoreEvents,
  } = useCarouselState(events, index);

  const navigate = useNavigate();

  const currentEvent = historyEvents[currentEventIndex];

  if (!currentEvent) {
    // Show a fallback UI or spinner during state transitions
    return <div>Loading...</div>;
  }

  const handleLoadLeft = async () => await loadMoreEvents("left", loadPrev);

  const handleLoadRight = async () => await loadMoreEvents("right", loadNext);

  const coords = currentEvent.map.locations.map((location) => ({
    latitude: location.latitude,
    longitude: location.longitude,
  }));

  const handleSearch = async (value: string) => {
    if (!value) {
      setSearchResults([]);
      return;
    }
    setLoading(true);
    try {
      const response = await debouncedSearchStories(value);
      setSearchResults(response?.results || []);
    } catch (error) {
      console.error('Failed to search stories:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
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
              options={searchResults}
              loading={loading}
              onInputChange={(_, value) => handleSearch(value)}
              getOptionLabel={(option) => 
                typeof option === 'string' ? option : option.name
              }
              renderOption={(props, option) => (
                <li {...props} onClick={() => navigate(`/stories/${option.id}`)}>
                  {option.name}
                </li>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Search for a story"
                  variant={"outlined"}
                  InputProps={{
                    ...params.InputProps,
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
              slides={historyEvents.map((event) => (
                <EventView event={event} />
              ))}
              setFocusedIndex={setCurrentEventIndex}
              startIndex={currentEventIndex}
              loadNext={handleLoadRight}
              loadPrev={handleLoadLeft}
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
    </Box>
  );
};

const buildUrlFor = (pointer: EventPointer) => {
  return `/stories/${pointer.storyId}/events/${pointer.id}`;
};
