import { IconButton } from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";

export const SettingsButton = () => {
  return (
    <IconButton
      size="large"
      edge="start"
      color="inherit"
      aria-label="settings"
      sx={{ mr: 2 }}
    >
      <SettingsIcon />
    </IconButton>
  );
};
