import { useQuery } from '@apollo/client';
import { useState, Dispatch, SetStateAction } from 'react';
import { Container, InputBox, SubmitButton, QueryResult, QueryResultButton } from './style';
import { GET_GUIDS_BY_NAME, GUIDsByNameResult, GUIDsByNameVars } from '../../graphql/queries';


interface SearchBarProps {
  handleEntityClick: Dispatch<SetStateAction<null | string>>;
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
    { variables: { name: queryText }
    })
  if (loading) return <h1>...loading</h1>
  if (error) return <h1>Error!</h1>
  console.log(data)
  return (
    <Container>
      <InputBox
        type="text"
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
      />
      <SubmitButton onClick={submitSearch}>Search</SubmitButton>
      <ul>
        {data && data.GetGUIDsByName.summaries.map(summary =>
          <QueryResult key={summary.guid}>
            <QueryResultButton
              onClick={() => handleEntityClick(summary.guid)}
              key={summary.guid}
            >{summary.type}: {summary.names} -- {summary.citation_count} citations,
             from {summary.first_citation_date} to {summary.last_citation_date}
            </QueryResultButton>
          </QueryResult>)}
      </ul>
    </Container>
  )
} 