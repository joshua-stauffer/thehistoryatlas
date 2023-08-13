import React from "react";
import {
  Box,
  Button,
  ButtonGroup,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from "@mui/material";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { HistoryEvent, Focus, Tag, EventPointer } from "../../graphql/events";
import { renderDateTime } from "../../components/renderDateTime/time";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { BiTimeFive } from "react-icons/bi";
import SearchIcon from "@mui/icons-material/Search";
import { TextButton } from "./buttons";
import { Link, useNavigate } from "react-router-dom";
import { sansSerifFont, serifFont } from "../../baseStyle";
import Autocomplete from "@mui/material/Autocomplete";
import Divider from "@mui/material/Divider";

interface EventViewProps {
  event: HistoryEvent;
  openTimeTravelModal: () => void;
}

const cardPadding = "1vh";
const cardSpacingInternal = "5px";

const citationSX = {
  fontSize: "12px",
};

export const EventView = (props: EventViewProps) => {
  const navigate = useNavigate();
  return (
    <Box
      sx={{
        marginTop: "auto",
        marginBottom: "auto",
        paddingTop: cardPadding,
        minHeight: "98vh",
        maxHeight: "1200px",
        padding: "20px",
      }}
    >
      <Autocomplete
        sx={{ fontFamily: sansSerifFont }}
        id="story-search"
        freeSolo
        options={props.event.tags.map((tag) => tag.name)}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Search for a story"
            variant={"outlined"}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        )}
      />
      <Typography
        variant={"h1"}
        sx={{ textAlign: "center", marginTop: "5vh", marginBottom: "2vh" }}
      >
        {props.event.story.name}
      </Typography>
      <ButtonGroup variant={"outlined"} sx={{ width: "100%" }}>
        <Button
          sx={{
            marginLeft: "auto",
          }}
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(buildUrlFor(props.event.prevEvent))}
          variant={"text"}
        >
          Previous Event
        </Button>
        <Button onClick={props.openTimeTravelModal} variant={"text"}>
          Jump To Time
        </Button>
        <Button
          sx={{ marginRight: "auto" }}
          endIcon={<ArrowForwardIcon />}
          onClick={() => navigate(buildUrlFor(props.event.nextEvent))}
          variant={"text"}
        >
          Next Event
        </Button>
      </ButtonGroup>
      <Divider
        sx={{
          marginTop: "10px",
          marginBottom: "10px",
        }}
      />
      <Typography textAlign={"center"}>
        {renderDateTime(props.event.date)}
      </Typography>
      <Typography
        variant={"body1"}
        textAlign="left"
        mt={"20px"}
        sx={{
          marginTop: cardSpacingInternal,
          marginBottom: cardSpacingInternal,
        }}
      >
        {buildTaggedText(props.event)}
      </Typography>

      <Typography variant={"body1"} mt={"20px"} sx={citationSX}>
        "{props.event.source.text}"
      </Typography>
      <Typography variant={"body1"} sx={citationSX}>
        -- {props.event.source.title} ({props.event.source.author})
      </Typography>
      <Divider
        sx={{
          marginTop: "20px",
          marginBottom: "20px",
        }}
      />
      <Typography variant={"body2"} fontSize={"18px"}>
        Other stories with this event
      </Typography>
      {props.event.relatedStories.map((story) => (
        <>
          <Link to={`/stories/${story.id}/events/${props.event.id}`}>
            <Button sx={{ textTransform: "none" }}>{story.name}</Button>
          </Link>
          <br />
        </>
      ))}
    </Box>
  );
};

const buildUrlFor = (pointer: EventPointer) => {
  return `/stories/${pointer.storyId}/events/${pointer.id}`;
};

const buildTaggedText = (
  event: HistoryEvent
): (string | JSX.Element | null)[] => {
  let tagIndices: Array<number> = [];
  for (const tag of event.tags) {
    const indices = Array.from(
      { length: tag.stopChar - tag.startChar },
      (_, i) => tag.startChar + i
    );
    tagIndices = [...tagIndices, ...indices];
  }
  const tagIndicesSet = new Set(tagIndices);
  const startCharMap: Map<number, Tag> = new Map(
    event.tags.map((tag) => [tag.startChar, tag])
  );
  return Array.from(event.text).map((char, index) => {
    const tag = startCharMap.get(index);
    if (!!tag) {
      const icon =
        tag.type === "PERSON" ? (
          <GoPerson />
        ) : tag.type === "PLACE" ? (
          <VscLocation />
        ) : (
          <BiTimeFive />
        );
      const storyUrl = `/stories/${tag.defaultStoryId}/events/${event.id}`;
      return (
        <Link to={storyUrl}>
          <TextButton text={tag.name} icon={icon} />
        </Link>
      );
    } else if (tagIndicesSet.has(index)) {
      return null;
    } else {
      return char;
    }
  });
};
