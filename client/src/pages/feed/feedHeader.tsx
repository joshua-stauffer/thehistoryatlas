import React from "react";
import {
  AppBar,
  Box,
  Button,
  IconButton,
  Toolbar,
  Typography,
} from "@mui/material";
import { MdMap, MdViewList } from "react-icons/md";
import { useAuth } from "../../auth/authContext";

interface FeedHeaderProps {
  mapMode: boolean;
  onToggleMapMode: () => void;
  onLoginClick: () => void;
}

export const FeedHeader: React.FC<FeedHeaderProps> = ({
  mapMode,
  onToggleMapMode,
  onLoginClick,
}) => {
  const { isLoggedIn, username, logout } = useAuth();

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: "background.paper",
        borderBottom: "1px solid rgba(0,0,0,0.08)",
      }}
    >
      <Toolbar
        sx={{
          justifyContent: "space-between",
          px: { xs: 1, sm: 2 },
          minHeight: { xs: 48, sm: 56 },
        }}
      >
        <Typography
          variant="h3"
          sx={{
            fontSize: { xs: "1rem", sm: "1.25rem" },
            color: "primary.dark",
            whiteSpace: "nowrap",
          }}
        >
          The History Atlas
        </Typography>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <IconButton
            onClick={onToggleMapMode}
            size="small"
            sx={{ color: "primary.main" }}
            aria-label={mapMode ? "Switch to list" : "Switch to map"}
          >
            {mapMode ? <MdViewList size={22} /> : <MdMap size={22} />}
          </IconButton>

          {isLoggedIn ? (
            <Button
              size="small"
              onClick={logout}
              sx={{ textTransform: "none", fontSize: "0.875rem" }}
            >
              {username}
            </Button>
          ) : (
            <Button
              size="small"
              variant="outlined"
              onClick={onLoginClick}
              sx={{ textTransform: "none", fontSize: "0.875rem" }}
            >
              Log in
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};
