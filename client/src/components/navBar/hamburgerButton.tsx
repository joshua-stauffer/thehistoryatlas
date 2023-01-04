import MenuIcon from "@mui/icons-material/Menu";
import { IconButton } from "@mui/material";

export const HamburgerButton = () => {
  return (
    <IconButton
      size="large"
      edge="start"
      color="inherit"
      aria-label="menu"
      sx={{ mr: 2 }}
    >
      <MenuIcon />
    </IconButton>
  );
};
