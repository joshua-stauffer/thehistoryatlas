import { useQuery } from "@apollo/client";
import { useState } from "react";
import {
  Container,
  InputBox,
  SubmitButton,
  QueryResult,
  QueryResultButton,
} from "./style";
import { prettifyType } from "../../pureFunctions/prettifyType";
import {
  GET_GUIDS_BY_NAME,
  GUIDsByNameResult,
  GUIDsByNameVars,
} from "../../graphql/queries";
import { HistoryEntity } from "../../types";
import { prettifyDate } from "../../pureFunctions/prettifyDate";

interface SearchBarProps {
  handleEntityClick: (entry: HistoryEntity) => void;
}

export const SearchBar = ({ handleEntityClick }: SearchBarProps) => {
  const [searchText, setSearchText] = useState("");
  const [queryText, setQueryText] = useState("");
  const submitSearch = (): void => {
    // creates query for current search term
    setQueryText(searchText);
    setSearchText("");
  };
  const { loading, error, data } = useQuery<GUIDsByNameResult, GUIDsByNameVars>(
    GET_GUIDS_BY_NAME,
    { variables: { name: queryText } }
  );
  if (loading) return <h1>...loading</h1>;
  if (error) return <h1>Error!</h1>;
  return (
    <Container>
      <InputBox
        type="text"
        value={searchText}
        autoFocus={true}
        onChange={(e) => setSearchText(e.target.value)}
      />
      <SubmitButton onClick={submitSearch}>Search</SubmitButton>
      <ul>
        {data ? (
          data.GetGUIDsByName.summaries.map((summary) => (
            <QueryResult key={summary.guid}>
              <QueryResultButton
                onClick={() =>
                  handleEntityClick({
                    entity: {
                      guid: summary.guid,
                      type: summary.type,
                      name: summary.names ? summary.names[0] : "",
                    },
                    rootEventID: undefined,
                  })
                }
                key={summary.guid}
              >
                <h1>{summary.names} </h1>
                <h2>{prettifyType(summary.type)}</h2>

                <h2>
                  {prettifyDate({ dateString: summary.first_citation_date })} -{" "}
                  {prettifyDate({ dateString: summary.last_citation_date })}
                </h2>
                <h3>Appears in {summary.citation_count} events.</h3>
              </QueryResultButton>
            </QueryResult>
          ))
        ) : (
          <li>Sorry, no results were found for that name.</li>
        )}
      </ul>
    </Container>
  );
};
