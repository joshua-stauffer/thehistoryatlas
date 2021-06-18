import styled from 'styled-components';

export const SummaryBox = styled.div`
  width: 500px;
  height: 200px;
  margin: 20px auto;
  background-color: white;
  border-radius: 5px;
  display: flex;
  justify-content: center;
  justify-items: center;
`

export const SummaryText = styled.p`
  margin: 10px;
  font-family: monospace;
  font-size: 1.2rem;
`

export const TimeTag = styled.button`
border: none;
background-color: inherit;
color: green; 
font-size: inherit;
font-family: inherit;
text-decoration: underline;
`

export const PersonTag = styled.button`
border: none;
background-color: inherit;
color: red;
font-size: inherit;
font-family: inherit;
text-decoration: underline;
`

export const PlaceTag = styled.button`
  border: none;
  background-color: inherit;
  color: blue;
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
  `