import styled from 'styled-components';

export const NavBar = styled.nav`
  width: 600px;
  height: 150px;
  margin-right: 30px;
  display: flex;
  justify-content: space-evenly;
  align-content: center;
`

export const NavButton = styled.button`
  border: solid 1px rgba(17, 17, 17, 0.25);
  border-radius: 5px;
  height: 50px;
  width: 200px;
  margin: auto auto;
  background-color: inherit;
  font-family: inherit;
`

export const ActiveNavButton = styled.button`
  border: none;
  border-radius: 5px;
  box-shadow: -1px 0px 1px 1px rgba(17, 17, 17, 0.25);
  height: 50px;
  width: 200px;
  margin: auto auto;
  background-color: inherit;
  font-family: inherit;
`

export const FocusHeader = styled.h2`
  width: 250px;
  padding: 0;
  margin: auto;
  text-align: center;
  font-size: 2rem;
`
