import { createTheme } from "@mui/material/styles";

export const serifFont = "Lora";
// const bookFont = "Bacasime Antique"
export const sansSerifFont = "Roboto";

export const theme = createTheme({
  typography: {
    fontFamily: sansSerifFont,
    h1: {
      fontSize: "40px",
      fontFamily: serifFont,
    },
    subtitle1: {
      fontSize: "25px",
    },
    body1: {
      fontSize: "18px",
      fontFamily: serifFont,
    },
    body2: {
      fontSize: "14px",
    },
  },
  palette: {
    mode: "light",

    primary: {
      main: "#00695c",
      light: "#2196f3",
      dark: "#757575",
    },
    secondary: {
      main: "#757575",
    },
  },
  // palette: {
  //   primary: {
  //     light: "#e1bee7",
  //     main: "#6a1b9a",
  //     dark: "#4a148c",
  //   },
  //   secondary: {
  //     light: "#ffb74d",
  //     main: "#ef6c00",
  //     dark: "#e65100",
  //   },
  //   error: {
  //     main: "#f44336",
  //   },
  //   warning: {
  //     main: "#ffa726",
  //   },
  //   info: {
  //     main: "#29b6f6",
  //   },
  //   success: {
  //     main: "#66bb6a",
  //   },
  //   contrastThreshold: 5,
  // },
  // typography: {
  //   button: {
  //     color: "secondary",
  //   },
  // },
});
