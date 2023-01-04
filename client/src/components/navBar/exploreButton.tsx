import { Button } from "@mui/material";
import { Link } from "react-router-dom";
import { theme } from "../../baseStyle";

export const ExploreButton = () => {
  return (
    <Link to="/">
      <Button sx={{ color: theme.palette.secondary.main }}>Explore</Button>
    </Link>
  );
};
