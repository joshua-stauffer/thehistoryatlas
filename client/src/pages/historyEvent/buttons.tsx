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
      disableRipple
      sx={{
        textTransform: "none",
        padding: 0,
        minWidth: "auto",
        lineHeight: "inherit",
        height: "auto",
        verticalAlign: "baseline",
        "&.MuiButton-root": {
          display: "inline",
          fontSize: "1.25rem",
        },
        "& .MuiButton-startIcon": {
          margin: 0,
          marginRight: "4px",
          display: "inline-flex",
          verticalAlign: "baseline",
        },
        "&:hover": {
          backgroundColor: "transparent",
          "& .MuiTypography-root": {
            color: "secondary.main",
            transition: "all 0.2s ease",
          },
        },
        ...props.sx,
      }}
      startIcon={props.icon}
    >
      <Typography
        variant={"body1"}
        component="span"
        sx={{
          display: "inline",
          lineHeight: "inherit",
          verticalAlign: "baseline",
          color: "#1A237E",
          fontWeight: 600,
          fontSize: "1.25rem",
          letterSpacing: "0.01em",
          transition: "all 0.2s ease",
          textDecoration: "none",
          "&:hover": {
            textDecoration: "none",
          },
        }}
      >
        {props.text}
      </Typography>
    </Button>
  );
};
