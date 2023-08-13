import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Hidden from "@mui/material/Hidden";
import { SingleEntityMap } from "../../components/singleEntityMap";
import { HistoryEventCard } from "./historyEventCard";

import { useState } from "react";
import { TimeTravelModal } from "./timeTravelModal";
import { StoryCard } from "./storyCard";
import { useLoaderData, useNavigate } from "react-router-dom";
import { HistoryEventData } from "./historyEventLoader";
import { SpeedDial, SpeedDialIcon } from "@mui/material";

export const HistoryEventView = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const handleOpen = () => setIsOpen(true);
  const handleClose = () => setIsOpen(false);
  const navigate = useNavigate();

  const { event: historyEvent } = useLoaderData() as HistoryEventData;

  const coords = historyEvent.map.locations.map((location) => {
    return {
      latitude: location.latitude,
      longitude: location.longitude,
    };
  });
  return (
    <Box sx={{ height: "96vh", maxHeight: "1000px" }}>
      <TimeTravelModal isOpen={isOpen} handleClose={handleClose} />
      <Grid container spacing={5} direction={"row"} justifyItems={"center"}>
        {/* Event Feed */}

        <Grid item sm={12} md={6}>
          {/* left box desktop, top box mobile */}

          <HistoryEventCard
            event={historyEvent}
            openTimeTravelModal={handleOpen}
          />
          <StoryCard event={historyEvent} />

          <Hidden mdUp>
            {/* Inline map for mobile */}
            <SingleEntityMap
              coords={coords}
              mapTyle={"natGeoWorld"}
              size={"SM"}
              title={historyEvent.map.locations[0].name}
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
              title={historyEvent.map.locations[0].name}
              zoom={7}
            />
          </Hidden>
        </Grid>
      </Grid>
      <SpeedDial
        ariaLabel="Add new Event"
        sx={{ position: "absolute", bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
        onClick={() => navigate("/add-event")}
      ></SpeedDial>
    </Box>
  );
};
