import { Button, SxProps, Theme, Typography } from "@mui/material";
import React from "react";

interface ButtonProps {
  text: string;
  icon?: JSX.Element | undefined;
  sx?: SxProps<Theme> | undefined;
}

export const TextButton = (props: ButtonProps) => {
  return (
    <Button
      variant={"text"}
      sx={{
        textTransform: "none",
        position: "relative",
        bottom: "2.5px",
        ...props.sx,
      }}
      startIcon={props.icon}
    >
      <Typography variant={"body1"}>{props.text}</Typography>
    </Button>
  );
};
