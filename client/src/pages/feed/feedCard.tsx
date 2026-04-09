import React, { useState } from "react";
import { Box, Card, CardContent, Chip, IconButton, Typography } from "@mui/material";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { BiTimeFive } from "react-icons/bi";
import { MdStar, MdStarBorder } from "react-icons/md";
import { useNavigate } from "react-router-dom";
import { FeedEvent } from "../../api/feed";
import { toggleFavorite } from "../../api/auth";
import { useAuth } from "../../auth/authContext";

interface FeedCardProps {
  event: FeedEvent;
}

export const FeedCard: React.FC<FeedCardProps> = ({ event }) => {
  const navigate = useNavigate();
  const { token, isLoggedIn } = useAuth();
  const [favorited, setFavorited] = useState(event.isFavorited);

  const personTag = event.tags.find((t) => t.type === "PERSON");
  const placeTag = event.tags.find((t) => t.type === "PLACE");
  const timeTag = event.tags.find((t) => t.type === "TIME");

  const handleViewStory = () => {
    if (personTag) {
      navigate(`/stories/${personTag.id}/events/${event.summaryId}`);
    }
  };

  const handleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isLoggedIn || !token) return;
    try {
      await toggleFavorite(event.summaryId, favorited, token);
      setFavorited(!favorited);
    } catch {
      // ignore
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
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          {event.themes.length > 0 ? (
            <Box sx={{ display: "flex", gap: 0.5, mb: 1, flexWrap: "wrap" }}>
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
          ) : (
            <Box />
          )}

          {isLoggedIn && (
            <IconButton
              size="small"
              onClick={handleFavorite}
              sx={{
                color: favorited ? "secondary.main" : "text.secondary",
                mt: -0.5,
                mr: -0.5,
              }}
              aria-label={favorited ? "Remove from favorites" : "Add to favorites"}
            >
              {favorited ? <MdStar size={20} /> : <MdStarBorder size={20} />}
            </IconButton>
          )}
        </Box>

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
