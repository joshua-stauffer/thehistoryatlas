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
import { EventView } from "./eventView";

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
    <Box sx={{ height: "92vh", maxHeight: "1000px" }}>
      <TimeTravelModal isOpen={isOpen} handleClose={handleClose} />
      <Grid container spacing={5} direction={"row"} justifyItems={"center"}>
        {/* Event Feed */}

        <Grid item sm={12} md={6}>
          {/* left box desktop, top box mobile */}

          <EventView event={historyEvent} openTimeTravelModal={handleOpen} />
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
        sx={{ position: "absolute", top: 16, right: 16 }}
        icon={<SpeedDialIcon />}
        onClick={() => navigate("/add-event")}
      ></SpeedDial>
    </Box>
  );
};
