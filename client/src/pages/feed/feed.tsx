import { Box, Grid, Paper, Divider } from '@mui/material';

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
import { PlaceTag } from '../../types';
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
      <Grid container>
        {
          currentSummaries.map((summary, i) => (
            <Paper sx={{ width: "100%", marginTop: "55px"}}>
              <Grid 
                item 
                id={`event-card-${i}`} 
                ref={feedRef} xs={12}
              >
                <Paper>
                  <FeedCard
                    summary={summary}
                    currentFocus={currentFocus}
                  />
                </Paper>
              </Grid>
              <Grid item id={`event-tags-${i}`}>
                <TagBox
                  tags={summary.tags}
                  setCurrentEntity={setCurrentEntity}
                />
              </Grid>
              <Grid item>
                  <SingleEntityMap
                    coords={getCoordsFromSummary(summary)}
                    mapTyle={"natGeoWorld"}
                    size={"LG"}
                    title={currentFocus.focusedGUID}
                    zoom={6}
                  />
              </Grid>
              <Grid item sm={12} height={50}>
                <Divider variant="middle"/>
              </Grid>
            </Paper>
          ))
        }
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