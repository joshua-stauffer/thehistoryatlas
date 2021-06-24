import { useState } from "react";
import { useQuery } from "@apollo/client";
import { HistoryEntity } from "../../types";
import { GUIDsByNameVars, GUIDsByNameResult, GET_GUIDS_BY_NAME} from "../../graphql/queries";
import { SearchButton, InputBox, Container, NavQueryResult, NavQueryResultButton, CloseButton } from "./style";

interface SearchBarProps {
  handleEntityClick: (entity: HistoryEntity) => void;
}


export const MenuSearch = ({ handleEntityClick }: SearchBarProps) => {
  const [ searchText, setSearchText ] = useState<string>('');
  const [queryText, setQueryText] = useState<string>('');
  const [ showResults, setShowResults ] = useState<boolean>(false);

  const submitSearch = (): void => {
    // creates query for current search term
    setQueryText(searchText)
    setSearchText('')
    setShowResults(true)
  }

  const wrappedClickHandler = (entity: HistoryEntity) => {
    setShowResults(false);
    handleEntityClick(entity)
  }

  const { loading, error, data } = useQuery<GUIDsByNameResult, GUIDsByNameVars>(
    GET_GUIDS_BY_NAME,
    { variables: { name: queryText } }
  )
  if (loading) return <h1>...loading</h1>
  if (error) return <h1>Error!</h1>
  return (
    <Container>
      <InputBox
        type="text"
        value={searchText}
        autoFocus={true}
        onChange={(e) => setSearchText(e.target.value)}
      />
      <SearchButton onClick={submitSearch}>Search</SearchButton>
      <ul>
        {data && showResults ? data.GetGUIDsByName.summaries.map(summary =>
          <NavQueryResult key={summary.guid}>
            <NavQueryResultButton
              onClick={() => wrappedClickHandler({
                entity: {
                  guid: summary.guid,
                  type: summary.type,
                  name: summary.names ? summary.names[0] : ''
                },
                rootEventID: undefined
              })}
              key={summary.guid}
            >{summary.names} ({summary.type})
            </NavQueryResultButton>
            <CloseButton onClick={() => setShowResults(false)}>x</CloseButton>
          </NavQueryResult>)
         : ''
        }
      </ul>
    </Container>
  )
}