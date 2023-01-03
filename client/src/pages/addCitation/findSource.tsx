import { useQuery } from "@apollo/client";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import { useState } from "react";
import {
  SearchSourcesResult,
  SearchSourcesVars,
  SEARCH_SOURCES,
} from "../../graphql/searchSource";
import { Source } from "./addCitationPage";

interface FindSourceProps {
  finishedSearch: () => void;
  addSource: (source: Source) => void;
}

export const FindSource = (props: FindSourceProps) => {
  const [searchInput, setSearchInput] = useState<string>("Bach");
  const { loading, error, data } = useQuery<
    SearchSourcesResult,
    SearchSourcesVars
  >(SEARCH_SOURCES, { variables: { searchTerm: searchInput } });

  if (loading) {
    return <p>Loading...</p>;
  }

  if (error) {
    return <p>Oops -- there was an error. Sorry, try again</p>;
  }
  const buildSource = (source: SearchSourcesResult["searchSources"][0]) => {
    const selectSourceHandler = () =>  props.addSource({
        id: source.id,
        title: source.title,
        publisher: source.publisher,
        author: source.author,
        pubDate: source.pubDate
      })
    return (
      <ListItem onClick={selectSourceHandler}>
        <ListItemText>Title: {source.title}</ListItemText>
        <ListItemText>Author: {source.author}</ListItemText>
        <ListItemText>Publisher: {source.publisher}</ListItemText>
        <ListItemText>Date Published: {source.pubDate}</ListItemText>
      </ListItem>
    )
  }

  return (
    <Paper>
      <List>
        {data?.searchSources &&
          data.searchSources.map((source) => buildSource(source))}
      </List>

      <Button onClick={props.finishedSearch}>Create New Entity</Button>
    </Paper>
  );
};
