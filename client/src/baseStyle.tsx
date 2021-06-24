import styled from "styled-components";

interface Theme {
  bg: string;
  fg: string;
}

interface ColorTheme {
  dark: Theme;
  light: Theme;
}

export const colorTheme: ColorTheme = {
  dark: {
    bg: '#FFFFFFF',
    fg: '#FFFFFFF'
  },
  light: {
    bg: '#fffff8',
    fg: '#111'
  }
}

export const Background = styled.div`

`
