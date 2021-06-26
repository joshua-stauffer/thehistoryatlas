import styled from 'styled-components';

const transparency = 1;
const summaryBoxHeight = 168;

const timeColor = '#007A00';
const personColor = '#00007A';
const placeColor = '#8F0000';

export const SummaryBox = styled.div`
  width: 450px;
  height: ${summaryBoxHeight}px;
  margin: 20px 20px;
  background-color: inherit;
  border-radius: 5px;
  display: flex;
  justify-content: center;
  justify-items: center;
  color: #111;
  position: relative;
`

export const SummaryText = styled.p`
  font-family: inherit;
  font-size: 1.2rem;
  color: rgba(17, 17, 17, ${transparency});
  line-height: 2rem;
`

export const TimeTag = styled.button`
  border: none;
  background-color: inherit;
  color: ${timeColor}; 
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
  color: ${personColor};
`

export const PlaceTag = styled.button`
  border: none;
  background-color: inherit;
  color: ${placeColor};
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
  `

export const SummaryHeader = styled.h3`
  font-family: inherit;
  color: rgba(17, 17, 17, ${transparency});
  margin: 10px 10px;
  width: 125px;
  line-height: 3
`

export const FocusedSummaryText = styled.p`
  font-family: inherit;
  font-size: 1.2rem;
  color: rgb(17, 17, 17);
  line-height: 2rem;
`

//

export const FocusedSummaryBox = styled.div`
  width: 450px;
  height: ${summaryBoxHeight}px;
  display: flex;
  justify-content: center;
  justify-items: center;
  margin: 20px 20px;
  background-color: inherit;
  border: none;
  border-radius: 5px;
  box-shadow: -1px 0px 1px 1px rgba(17, 17, 17, 0.25);
  position: relative;
`
// 

export const FocusedSummaryHeader = styled.h3`
  font-family: inherit;
  color: #111;
  margin: 10px 10px;
  width: 125px;
  line-height: 3
`

export const FocusedTimeTag = styled.button`
  border: none;
  background-color: inherit;
  color: ${timeColor}; 
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
`

export const FocusedPersonTag = styled.button`
  border: none;
  background-color: inherit;
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
  color: ${personColor};
`

export const FocusedPlaceTag = styled.button`
  border: none;
  background-color: inherit;
  color: ${placeColor};
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
`

export const CitationButton = styled.button`
  background-color: inherit;
  font-family: inherit;
  width: 100px;
  border: none;
  position: absolute;
  top: 135px;
  right: 50px;
`

export const CitationContainer = styled.div`
  position: absolute;
  padding: 10px;
  width: 430px;
  height: auto;
  max-height: 400px;
  overflow-y: scroll;
  top: 171px;
  border: none;
  border-radius: 5px;

  box-shadow: -1px 0px 1px 1px rgba(17, 17, 17, 0.25);
  background-color: #fffff8;
  z-index: 5;
`

export const CitationText = styled.p`
  font-size: 1.2rem;
`