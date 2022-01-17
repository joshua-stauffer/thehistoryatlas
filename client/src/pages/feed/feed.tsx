import { Box, Grid, Paper, Divider, Hidden } from '@mui/material';

import { useFeedLogic } from './feedLogic';
import {
  NavBar,
  SettingsButton,
  LoginButton,
  AddCitationButton
} from '../../components/navBar';
import { SearchBar } from './searchBar';
import { FeedCard } from './feedCard';
import { SingleEntityMap } from '../../components/singleEntityMap';
import { TagBox } from './tagBox';
import { MarkerData } from '../../types';
import { Summary } from '../../graphql/getSummariesByGUID'

interface FeedProps {

}

export const FeedPage = (props: FeedProps) => {

  const {
    feedRef,
    currentDate,
    handleTimelineClick,
    resetCurrentEvents,
    setCurrentEntity,
    currentFocus,
    currentCoords,
    focusedGeoEntities,
    currentSummaries
  } = useFeedLogic()

  return (
    <Box sx={{ flexGrow: 1 }}>
      <NavBar children={[
        <SearchBar />,
        <AddCitationButton />,
        <LoginButton />,
        <SettingsButton />
      ]} />
      <Box sx={{ height: 70 }}></Box>
      <Grid
        container
        spacing={10}
        direction={"row"}
        justifyItems={"center"}
      >
        {/* Event Feed */}
        <Grid item
          sm={12}
          md={6}
          sx={{
            maxHeight: "100vh",
            overflow: "scroll",
          }}
          ref={feedRef}
        >
          {
            currentSummaries.map((summary, i) => (

              <Paper sx={{ marginTop: "55px" }}>
                <Grid
                  item
                  id={`event-card-${i}`}
                  xs={12}
                  md={12}
                >
                  <Paper
                    sx={{
                      border: currentFocus.focusedGUID === summary.guid ? "solid red 1px" : null
                    }}>
                    <FeedCard
                      summary={summary}
                      currentFocus={currentFocus}
                    />
                  </Paper>
                </Grid>
                <Grid
                  item
                  xs={12}
                  md={12}
                  id={`event-tags-${i}`}
                >
                  <TagBox
                    tags={summary.tags}
                    setCurrentEntity={setCurrentEntity}
                  />
                </Grid>
                <Hidden mdUp>
                  {/* Inline map for mobile */}
                  <Grid
                    item
                    sm={12}
                  >
                    <SingleEntityMap
                      coords={getCoordsFromSummary(summary)}
                      mapTyle={"natGeoWorld"}
                      size={"SM"}
                      title={currentFocus.focusedGUID}
                      zoom={6}
                    />
                  </Grid>
                </Hidden>
              </Paper>
            ))
          }
        <Grid item 
          sx={{
            height: "70vh"
          }}
        >
          {/* Spacer for the end of the feed */}
        </Grid>
        </Grid>
        <Hidden smDown>
          {/* Standalone map for desktop */}
          <Grid item md={6}>
            <SingleEntityMap
              coords={focusedGeoEntities.map(entity => entity.coords) ?? getCoordsFromCurrentCoords(currentCoords)}
              mapTyle={"natGeoWorld"}
              size={"MD"}
              title={currentFocus.focusedGUID}
              zoom={6}
            />
          </Grid>
        </Hidden>
      </Grid>
    </Box>
  );
}

type Coords = {
  latitude: number;
  longitude: number;
}[]

const getCoordsFromSummary = (summary: Summary): Coords => {
  const coords: Coords = []
  for (const tag of summary.tags) {
    if (tag.tag_type === "PLACE") {
      coords.push(tag.coords)
    }
  }
  return coords
}

const getCoordsFromCurrentCoords = (markerData: MarkerData[]): Coords => {
  console.log({ markerData })
  return markerData.map(marker => marker.coordsObj)
}
