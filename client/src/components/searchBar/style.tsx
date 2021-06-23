import styled from 'styled-components';


export const Container = styled.div`
  height: 300px;
  width: 500px;
  //border: solid 2px black;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: auto auto;
`

export const InputBox = styled.input`
  width: 200px;
  display: block;
  margin: 20px;
`

export const SubmitButton = styled.button`
  height: 20px;
  width: 100px;
  border: solid 1px;
  background-color: white;
  font-family: inherit;
`

export const QueryResult = styled.li`
  list-style: none;
`

export const QueryResultButton = styled.button`
  border: solid 1px darkgray;
  background-color: white;
`