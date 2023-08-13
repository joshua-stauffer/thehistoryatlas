import { useQuery } from "@apollo/client";
import { InputAdornment, Skeleton, TextField, Typography } from "@mui/material";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Input from "@mui/material/Input";
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
import { Source } from "./addEventPage";

interface FindSourceProps {
  finishedSearch: () => void;
  addSource: (source: Source) => void;
}

export const FindSource = (props: FindSourceProps) => {
  const [searchInput, setSearchInput] = useState<string>("");
  const handleSearchInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInput(event.target.value);
  };
  const { loading, error, data } = useQuery<
    SearchSourcesResult,
    SearchSourcesVars
  >(SEARCH_SOURCES, { variables: { searchTerm: searchInput } });

  const buildSource = (source: SearchSourcesResult["searchSources"][0]) => {
    const selectSourceHandler = () =>
      props.addSource({
        id: source.id,
        title: source.title,
        publisher: source.publisher,
        author: source.author,
        pubDate: source.pubDate,
      });
    return (
      <ListItem>
        <Paper
          sx={{
            width: "400px",
            height: "300px",
            margin: "20px",
            padding: "20px",
            border: "solid 1px white",
            "&:hover": {
              // TODO: change Paper elevation instead of border
              border: "solid 1px grey",
            },
          }}
          onClick={selectSourceHandler}
        >
          <ListItemText>Title: {source.title}</ListItemText>
          <ListItemText>Author: {source.author}</ListItemText>
          <ListItemText>Publisher: {source.publisher}</ListItemText>
          <ListItemText>Date Published: {source.pubDate}</ListItemText>
        </Paper>
      </ListItem>
    );
  };

  return (
    <Paper
      sx={{
        padding: "20px",
        margin: "50px",
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          width: "100%",
        }}
      >
        <TextField
          label={"Search for Source by Title or Author"}
          variant="outlined"
          value={searchInput}
          onChange={handleSearchInput}
          sx={{
            width: "400px",
          }}
          InputProps={{
            endAdornment: loading ? (
              <InputAdornment position="end">...loading</InputAdornment>
            ) : null,
          }}
        />
      </Box>
      <List
        sx={{
          display: "flex",
          justifyContent: "center",
          gap: "100px",
          width: "100%",
        }}
      >
        {!data?.searchSources || data.searchSources.length === 0 ? (
          <Box
            sx={{
              width: "100%",
              height: "318px",
              margin: "20px",
              padding: "20px",
            }}
          />
        ) : (
          data.searchSources.map((source) => buildSource(source))
        )}
      </List>
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          width: "100%",
        }}
      >
        <Typography
          variant="body1"
          sx={{ lineHeight: "100px", marginRight: "20px" }}
        >
          Not finding the source you're looking for?
        </Typography>
        <Button onClick={props.finishedSearch}>Create New Source</Button>
      </Box>
    </Paper>
  );
};
