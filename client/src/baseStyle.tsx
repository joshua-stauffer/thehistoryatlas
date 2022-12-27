import { createTheme } from "@mui/material/styles";

// interface Theme {
//   primary: string;
//   secondary: string;
// }

// interface ColorTheme {
//   dark: Theme;
//   light: Theme;
// }

// export const colorTheme: ColorTheme = {
//   dark: {
//     primary: '#6a1b9a',
//     secondary: '#ef6c00'
//   },
//   light: {
//     primary: '#e1bee7',
//     secondary: '#ffb74d'
//   }
// }



// const CustomButton = styled(Button)(({ theme }) => ({
//   color: theme.palette.primary,
//   '&.MuiButton-containedPrimary': {
//     color: theme.palette.primary,
//   },
// }));

export const theme = createTheme({
  palette: {
    primary: {
      light: '#e1bee7',
      main: '#6a1b9a',
      dark: '#4a148c'
    },
    secondary: {
      light: '#ffb74d',
      main: '#ef6c00',
      dark: '#e65100'
    },
    error: {
      main: '#f44336'
    },
    warning: {
      main: '#ffa726'
    },
    info: {
      main: '#29b6f6'
    },
    success: {
      main: '#66bb6a'
    },
    contrastThreshold: 5,
  },
  typography: {
    button: {
      color: 'secondary'
    }
  }
})
