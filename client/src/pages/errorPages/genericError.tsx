import { Typography, Box, Paper } from "@mui/material";
export const GenericError = () => {
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
        Uh oh..
      </Typography>
      <Typography
        variant="h6"
        sx={{
          textAlign: "center",
          margin: "50px",
        }}
      >
        The History Atlas is temporarily unavailable.
      </Typography>
      <Typography
        variant="body1"
        sx={{
          textAlign: "center",
        }}
      >
        This might be because you're not connected to the internet, or because
        we're making improvements. Please try again soon!
      </Typography>
    </Box>
  );
};
