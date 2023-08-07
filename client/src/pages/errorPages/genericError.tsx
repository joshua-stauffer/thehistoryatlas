import { Typography, Box, Paper } from "@mui/material";

interface GenericErrorProps {
  header?: string | undefined;
  text?: string | undefined;
  details?: string | undefined;
}

export const GenericError = (props: GenericErrorProps) => {
  const headerFallback = "Uh oh..";
  const textFallback = "The History Atlas is temporarily unavailable.";
  const detailsFallback =
    "This might be because you're not connected to the internet, or because\n" +
    "        we're making improvements. Please try again soon!";
  return (
    <Box
      sx={{
        padding: "20px",
      }}
    >
      <Typography
        variant="h1"
        sx={{
          textAlign: "center",
          margin: "100px",
        }}
      >
        {props.header || headerFallback}
      </Typography>
      <Typography
        variant="h6"
        sx={{
          textAlign: "center",
          margin: "50px",
        }}
      >
        {props.text || textFallback}
      </Typography>
      <Typography
        variant="body1"
        sx={{
          textAlign: "center",
        }}
      >
        {props.details || detailsFallback}
      </Typography>
    </Box>
  );
};
