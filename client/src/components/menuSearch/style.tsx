import styled from "styled-components";

export const SearchButton = styled.button`
  border: none;
  color: inherit;
  background-color: inherit;
  margin: 0;
  font-family: inherit;
`;

export const InputBox = styled.input`
  width: auto;
  margin: 20px;
  font-family: inherit;
`;

export const Container = styled.div`
  width: auto;
  border: none;
  position: absolute;
  top: 25px;
  right: 100px;
`;

export const NavQueryResult = styled.div`
  position: absolute;
  border: none;
  box-shadow: -1px 0px 1px 1px rgba(17, 17, 17, 0.25);
  width: 100%;
  right: 0px;
  top: 50px;
  display: flex;
  justify-content: space-between;
`;

export const NavQueryResultButton = styled.button`
  font-family: inherit;
  background-color: inherit;
  border: none;
  font-size: 1.2rem;
`;

export const CloseButton = styled.button`
  background-color: inherit;
  font-family: inherit;
  border: none;
  font-size: 1.2rem;
`;
