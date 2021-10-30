import styled from "styled-components";

export const Container = styled.div`
  width: 85%;
  border: none;
  box-shadow: -1px 0px 1px 1px rgba(17, 17, 17, 0.25);
`
export const Panel = styled.div`
  width: 40%;
  border: solid 3px rgba(17, 17, 17, 0.25);
  margin: 5%;
  padding: 2%;
`

export const PanelContainer = styled.div`
display: flex;

`

export const TextBox = styled.textarea`
  border: solid 3px rgba(17, 17, 17, 0.25);
  background-color: inherit;
  border-radius: 5px 5px;
  width: 97%;
  height: 200px;
`

export const Input = styled.input`
border: solid 3px rgba(17, 17, 17, 0.25);
background-color: inherit;
border-radius: 5px 5px;
`

export const Button = styled.button`
  border: solid 1px rgba(17, 17, 17, 0.25);
  box-shadow: -1px 0px 1px 1px rgba(17, 17, 17, 0.25);
  width: 150px;
  height: 50px;
  background-color: inherit;
  font-family: inherit;
`

export const ControlBarNav = styled.nav`
  border: solid 1px rgba(17, 17, 17, 0.25);
  height: 50px;
  display: flex;
  justify-content: space-between;
  padding: 5px;
`