import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Hidden from "@mui/material/Hidden";
import { SingleEntityMap } from "../../components/singleEntityMap";
import React, { useState } from "react";
import { useLoaderData, useNavigate } from "react-router-dom";
import { HistoryEventData } from "./historyEventLoader";
import { InputAdornment, TextField, Typography, Button, CircularProgress, IconButton } from "@mui/material";
import { EventView } from "./eventView";
import Autocomplete from "@mui/material/Autocomplete";
import { sansSerifFont } from "../../baseStyle";
import SearchIcon from "@mui/icons-material/Search";
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
  const [searchValue, setSearchValue] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);

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
      if ((response?.results || []).length > 0) {
        setDropdownOpen(true);
      }
    } catch (error) {
      console.error("Failed to search stories:", error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchButtonClick = () => {
    handleSearch(searchValue);
  };

  return (
    <Box
      sx={{
        height: { xs: "auto", sm: "92vh" },
        maxHeight: { xs: "none", sm: "1000px" },
        overflow: "auto",
        width: "100%",
      }}
    >
      <Grid
        container
        spacing={{ xs: 2, sm: 3, md: 5 }}
        direction={"row"}
        justifyItems={"center"}
        sx={{
          margin: 0,
          width: "100%",
          padding: { xs: "0px", sm: "8px" },
        }}
      >
        <Grid item xs={12} sm={12} md={6} sx={{ width: "100%" }}>
          {/* left box desktop, top box mobile */}
          <Box
            sx={{
              marginTop: { xs: "1vh", sm: "auto" },
              marginBottom: { xs: "1vh", sm: "auto" },
              paddingTop: { xs: "2vh", sm: "1vh" },
              minHeight: { xs: "auto", sm: "92vh" },
              maxHeight: { xs: "none", sm: "1200px" },
              padding: { xs: "8px", sm: "20px" },
              overflow: "auto",
              width: "100%",
            }}
          >
            <Autocomplete
              sx={{ fontFamily: sansSerifFont }}
              id="story-search"
              freeSolo
              options={searchResults}
              loading={loading}
              onInputChange={(_, value) => setSearchValue(value)}
              getOptionLabel={(option) =>
                typeof option === "string" ? option : option.name
              }
              onChange={(_, value) => {
                if (value && typeof value !== 'string') {
                  navigate(`/stories/${value.id}`);
                }
              }}
              disableClearable={true}
              open={dropdownOpen}
              onOpen={() => setDropdownOpen(true)}
              onClose={() => setDropdownOpen(false)}
              renderOption={(props, option) => (
                <li {...props}>
                  {option.name}
                </li>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Search for a story"
                  variant={"outlined"}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleSearch(searchValue);
                    }
                  }}
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: (
                      <InputAdornment position="start">
                        {loading ? <CircularProgress size={20} /> : <SearchIcon />}
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <Button 
                        onClick={handleSearchButtonClick}
                        disabled={loading || !searchValue}
                        sx={{ minWidth: '64px', ml: 1 }}
                        variant="contained"
                        color="primary"
                      >
                        Search
                      </Button>
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
            {currentEvent.description && (
              <Typography
                variant={"subtitle1"}
                sx={{
                  textAlign: "center",
                  marginBottom: "3vh",
                  maxWidth: "800px",
                  margin: "0 auto 3vh",
                  color: "#4A5568",
                  fontStyle: "italic",
                  lineHeight: 1.6,
                  padding: "0 20px",
                }}
              >
                {currentEvent.description}
              </Typography>
            )}
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
