import { useQuery } from '@apollo/client';
import { useState } from 'react';
import { Container, InputBox, SubmitButton, QueryResult, QueryResultButton } from './style';
import { GET_GUIDS_BY_NAME, GUIDsByNameResult, GUIDsByNameVars } from '../../graphql/queries';
import { HistoryEntity } from '../../types';

interface SearchBarProps {
  handleEntityClick: (entry: HistoryEntity) => void;
}

export const SearchBar = ({ handleEntityClick }: SearchBarProps) => {
  const [searchText, setSearchText] = useState('')
  const [queryText, setQueryText] = useState('')
  const submitSearch = (): void => {
    // creates query for current search term
    setQueryText(searchText)
    setSearchText('')
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
        onChange={(e) => setSearchText(e.target.value)}
      />
      <SubmitButton onClick={submitSearch}>Search</SubmitButton>
      <ul>
        {data ? data.GetGUIDsByName.summaries.map(summary =>
          <QueryResult key={summary.guid}>
            <QueryResultButton
              onClick={() => handleEntityClick({
                entity: {
                  guid: summary.guid,
                  type: summary.type,
                  name: summary.names ? summary.names[0] : ''
                },
                rootEventID: undefined
              })}
              key={summary.guid}
            >{summary.type}: {summary.names} -- {summary.citation_count} citations,
             from {summary.first_citation_date} to {summary.last_citation_date}
            </QueryResultButton>
          </QueryResult>)
         : <li>Sorry, no results were found for that name.</li>
        }
      </ul>
    </Container>
  )
}