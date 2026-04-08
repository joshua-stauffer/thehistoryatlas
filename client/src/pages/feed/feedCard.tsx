import React from "react";
import { Box, Card, CardContent, Chip, Typography } from "@mui/material";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { BiTimeFive } from "react-icons/bi";
import { useNavigate } from "react-router-dom";
import { FeedEvent } from "../../api/feed";

interface FeedCardProps {
  event: FeedEvent;
}

export const FeedCard: React.FC<FeedCardProps> = ({ event }) => {
  const navigate = useNavigate();

  const personTag = event.tags.find((t) => t.type === "PERSON");
  const placeTag = event.tags.find((t) => t.type === "PLACE");
  const timeTag = event.tags.find((t) => t.type === "TIME");

  const handleViewStory = () => {
    // Find story via the first person tag's default story
    // For now navigate to the event via the history view
    if (personTag) {
      navigate(`/?eventId=${event.summaryId}`);
    }
  };

  return (
    <Card
      sx={{
        mb: 2,
        cursor: "pointer",
        "&:hover": {
          boxShadow: "0 4px 20px rgba(0,0,0,0.12)",
        },
      }}
      onClick={handleViewStory}
    >
      <CardContent sx={{ pb: "12px !important" }}>
        {event.themes.length > 0 && (
          <Box sx={{ display: "flex", gap: 0.5, mb: 1 }}>
            {event.themes.map((theme) => (
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

        <Typography
          variant="body1"
          sx={{
            mb: 1.5,
            display: "-webkit-box",
            WebkitLineClamp: 4,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {event.summaryText}
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
          {personTag && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <GoPerson size={14} />
              <Typography variant="body2" component="span">
                {personTag.name}
              </Typography>
            </Box>
          )}
          {placeTag && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <VscLocation size={14} />
              <Typography variant="body2" component="span">
                {placeTag.name}
              </Typography>
            </Box>
          )}
          {timeTag && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              <BiTimeFive size={14} />
              <Typography variant="body2" component="span">
                {timeTag.name}
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};
