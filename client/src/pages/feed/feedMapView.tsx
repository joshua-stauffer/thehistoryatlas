import React, { useState } from "react";
import { Box, Typography, Paper, Chip } from "@mui/material";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
} from "react-leaflet";
import L from "leaflet";
import { useNavigate } from "react-router-dom";
import { FeedEvent } from "../../api/feed";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { BiTimeFive } from "react-icons/bi";

interface FeedMapViewProps {
  events: FeedEvent[];
}

const eventIcon = L.divIcon({
  className: "feed-event-flag",
  html: "<div></div>",
  iconSize: [12, 12],
  iconAnchor: [6, 6],
  popupAnchor: [0, -8],
});

export const FeedMapView: React.FC<FeedMapViewProps> = ({ events }) => {
  const navigate = useNavigate();
  const [selectedEvent, setSelectedEvent] = useState<FeedEvent | null>(null);

  const mappableEvents = events.filter(
    (e) => e.latitude != null && e.longitude != null,
  );

  // Center on first event, or default to Europe
  const center: [number, number] =
    mappableEvents.length > 0
      ? [mappableEvents[0].latitude!, mappableEvents[0].longitude!]
      : [48.8, 10.0];

  return (
    <Box sx={{ position: "relative" }}>
      <MapContainer
        center={center}
        zoom={4}
        scrollWheelZoom={true}
        style={{ height: "60vh", width: "100%", borderRadius: 4 }}
      >
        <TileLayer
          attribution="Tiles &copy; Esri"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
        />
        {mappableEvents.map((event) => (
          <Marker
            key={event.summaryId}
            position={[event.latitude!, event.longitude!]}
            icon={eventIcon}
            eventHandlers={{
              click: () => setSelectedEvent(event),
            }}
          >
            <Popup>
              <div style={{ maxWidth: 240, fontSize: "0.85em" }}>
                <div style={{ marginBottom: 4 }}>
                  {event.summaryText.slice(0, 120)}
                  {event.summaryText.length > 120 ? "..." : ""}
                </div>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    const personTag = event.tags.find(
                      (t) => t.type === "PERSON",
                    );
                    if (personTag) {
                      navigate(
                        `/stories/${personTag.id}/events/${event.summaryId}`,
                      );
                    }
                  }}
                  style={{ fontSize: "0.85em" }}
                >
                  View story
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {selectedEvent && (
        <Paper
          elevation={3}
          sx={{
            mt: 2,
            p: 2,
            cursor: "pointer",
          }}
          onClick={() => {
            const personTag = selectedEvent.tags.find(
              (t) => t.type === "PERSON",
            );
            if (personTag) {
              navigate(
                `/stories/${personTag.id}/events/${selectedEvent.summaryId}`,
              );
            }
          }}
        >
          {selectedEvent.themes.length > 0 && (
            <Box sx={{ display: "flex", gap: 0.5, mb: 1 }}>
              {selectedEvent.themes.map((theme) => (
                <Chip
                  key={theme.slug}
                  label={theme.name}
                  size="small"
                  sx={{
                    fontSize: "0.75rem",
                    height: 24,
                    backgroundColor: "rgba(142, 68, 173, 0.1)",
                    color: "secondary.main",
                    fontWeight: 600,
                  }}
                />
              ))}
            </Box>
          )}

          <Typography variant="body1" sx={{ mb: 1 }}>
            {selectedEvent.summaryText}
          </Typography>

          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 2,
              color: "text.secondary",
              fontSize: "0.875rem",
            }}
          >
            {selectedEvent.tags
              .filter((t) => t.type === "PERSON")
              .slice(0, 1)
              .map((t) => (
                <Box
                  key={t.id}
                  sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                >
                  <GoPerson size={14} />
                  <Typography variant="body2" component="span">
                    {t.name}
                  </Typography>
                </Box>
              ))}
            {selectedEvent.tags
              .filter((t) => t.type === "PLACE")
              .slice(0, 1)
              .map((t) => (
                <Box
                  key={t.id}
                  sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                >
                  <VscLocation size={14} />
                  <Typography variant="body2" component="span">
                    {t.name}
                  </Typography>
                </Box>
              ))}
            {selectedEvent.tags
              .filter((t) => t.type === "TIME")
              .slice(0, 1)
              .map((t) => (
                <Box
                  key={t.id}
                  sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                >
                  <BiTimeFive size={14} />
                  <Typography variant="body2" component="span">
                    {t.name}
                  </Typography>
                </Box>
              ))}
          </Box>
        </Paper>
      )}

      {mappableEvents.length === 0 && (
        <Typography
          variant="body2"
          sx={{ textAlign: "center", py: 4, color: "text.secondary" }}
        >
          No events with coordinates to display on the map.
        </Typography>
      )}
    </Box>
  );
};
