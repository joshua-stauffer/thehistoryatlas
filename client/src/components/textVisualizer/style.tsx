import styled, { css } from "styled-components";

export const Container = styled.div`
  height: 300px;
  width: 500px;
  border: solid 2px black;
`;

export const AnnotateButton = styled.button`
  height: 20px;
  width: 40px;
  border: solid 1px;
  border-radius: 5px 5px 5px;
`;

const Word = css`
  line-height: 2rem;
  display: inline-block;
  border-radius: 7px 7px 7px;
  padding: 5px;
`;

export const NonEntity = styled.span`
  ${Word}
  color: black;
  background-color: white;
`;

export const Place = styled.span`
  ${Word}
  color: white;
  background-color: blue;
`;
