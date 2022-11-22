import styled from "styled-components";

interface Theme {
  primary: string;
  secondary: string;
}

interface ColorTheme {
  dark: Theme;
  light: Theme;
}

export const colorTheme: ColorTheme = {
  dark: {
    primary: '#6a1b9a',
    secondary: '#ef6c00'
  },
  light: {
    primary: '#e1bee7',
    secondary: '#ffb74d'
  }
}

export const Background = styled.div`

`
