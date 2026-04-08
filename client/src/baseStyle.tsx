import { createTheme } from "@mui/material/styles";

export const serifFont = "'Libre Baskerville', 'Times New Roman', serif";
export const sansSerifFont = "'Source Sans Pro', 'Helvetica Neue', sans-serif";
export const displayFont = "'Playfair Display', serif";

export const theme = createTheme({
  typography: {
    fontFamily: sansSerifFont,
    h1: {
      fontSize: "2.5rem",
      fontFamily: displayFont,
      fontWeight: 700,
      color: "#2C3E50",
      letterSpacing: "-0.02em",
      marginBottom: "1rem",
    },
    h2: {
      fontSize: "2rem",
      fontFamily: displayFont,
      fontWeight: 600,
      color: "#34495E",
      letterSpacing: "-0.01em",
    },
    h3: {
      fontSize: "1.75rem",
      fontFamily: displayFont,
      fontWeight: 600,
      color: "#34495E",
    },
    subtitle1: {
      fontSize: "1.25rem",
      fontFamily: serifFont,
      color: "#5D6D7E",
      lineHeight: 1.6,
    },
    body1: {
      fontSize: "1.125rem",
      fontFamily: serifFont,
      lineHeight: 1.8,
      color: "#2C3E50",
    },
    body2: {
      fontSize: "1rem",
      fontFamily: sansSerifFont,
      lineHeight: 1.6,
      color: "#5D6D7E",
    },
  },
  palette: {
    mode: "light",
    background: {
      default: "#FCFCFC",
      paper: "#FFFFFF",
    },
    primary: {
      main: "#34495E",
      light: "#5D6D7E",
      dark: "#2C3E50",
    },
    secondary: {
      main: "#8E44AD",
      light: "#9B59B6",
      dark: "#703688",
    },
    text: {
      primary: "#2C3E50",
      secondary: "#5D6D7E",
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: "1px solid rgba(0,0,0,0.08)",
          transition: "all 0.3s ease",
          "&:hover": {
            boxShadow: "0 4px 20px rgba(0,0,0,0.12)",
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontFamily: sansSerifFont,
          fontWeight: 600,
          borderRadius: 4,
          padding: "8px 24px",
        },
      },
    },
  },
});
