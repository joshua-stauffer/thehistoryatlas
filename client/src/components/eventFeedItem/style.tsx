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

export const FocusedSummaryBox = styled.div`
  width: 500px;
  height: 200px;
  margin: 20px auto;
  background-color: white;
  display: flex;
  justify-content: center;
  justify-items: center;
  border-left: solid 2px gray;
  border-right: solid 2px gray;
`

export const SummaryText = styled.p`
  font-family: inherit;
  font-size: 1.2rem;
  color: charcoal;
  line-height: 2rem;
`

export const TimeTag = styled.button`
  border: none;
  background-color: inherit;
  color: darkgreen; 
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
`

export const PersonTag = styled.button`
border: none;
background-color: inherit;
color: darkred;
font-size: inherit;
font-family: inherit;
text-decoration: underline;
`

export const PlaceTag = styled.button`
  border: none;
  background-color: inherit;
  color: darkblue;
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
  `

export const SummaryHeader = styled.h3`
  font-family: inherit;
  width: 150px;
  color: charcoal;
  margin: 10px;
`