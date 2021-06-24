import styled from 'styled-components';

export const SummaryBox = styled.div`
  width: 450px;
  height: 200px;
  margin: 20px 20px;
  background-color: inherit;
  border-radius: 5px;
  display: flex;
  justify-content: center;
  justify-items: center;
`

export const FocusedSummaryBox = styled.div`
  width: 450px;
  height: 200px;
  display: flex;
  justify-content: center;
  justify-items: center;
  margin-left: 20px;
  margin: 20px auto;
  background-color: inherit;
  border: solid 1px #FFFFF1;
  border-radius: 5px;
  box-shadow: -2px 0px 2px 1px #111;
`

export const SummaryText = styled.p`
  font-family: inherit;
  font-size: 1.2rem;
  color: #111;
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
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
  color: darkred
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
  color: #111;
  margin: 10px 10px;
  width: 125px;
  line-height: 3
`