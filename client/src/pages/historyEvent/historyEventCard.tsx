import React from "react";
import {
  Box,
  Button,
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
import { sansSerifFont } from "../../baseStyle";
import Autocomplete from "@mui/material/Autocomplete";

interface HistoryEventCardProps {
  event: HistoryEvent;
  openTimeTravelModal: () => void;
}

const cardPadding = "1vh";
const cardSpacingInternal = "5px";

const citationSX = {
  fontSize: "12px",
};

export const HistoryEventCard = (props: HistoryEventCardProps) => {
  const navigate = useNavigate();
  return (
    <Card
      sx={{
        marginTop: "auto",
        marginBottom: "auto",
        paddingTop: cardPadding,
        minHeight: "65vh",
        maxHeight: "1200px",
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
      <CardHeader
        sx={{ textAlign: "center" }}
        titleTypographyProps={{ variant: "h1" }}
        title={props.event.story.name}
        subheader={renderDateTime(props.event.date)}
      />
      <CardActions disableSpacing>
        <IconButton
          sx={{
            marginLeft: "auto",
            marginRight: "auto",
            marginTop: cardSpacingInternal,
            marginBottom: cardSpacingInternal,
          }}
          onClick={() => navigate(buildUrlFor(props.event.prevEvent))}
        >
          <ArrowBackIcon />
        </IconButton>
        <Button
          sx={{ textTransform: "none" }}
          startIcon={<SearchIcon />}
          onClick={props.openTimeTravelModal}
        >
          Jump To Time
        </Button>
        <IconButton
          sx={{ marginLeft: "auto", marginRight: "auto" }}
          onClick={() => navigate(buildUrlFor(props.event.nextEvent))}
        >
          <ArrowForwardIcon />
        </IconButton>
      </CardActions>

      <CardContent>
        <Typography
          variant={"body1"}
          textAlign="center"
          sx={{
            marginTop: cardSpacingInternal,
            marginBottom: cardSpacingInternal,
          }}
        >
          {buildTaggedText(props.event)}
        </Typography>
      </CardContent>
      <CardContent
        sx={{
          marginLeft: "40px",
          marginRight: "40px",
          marginBottom: cardSpacingInternal,
          marginTop: 0,
        }}
      >
        <Typography variant={"body1"} sx={citationSX}>
          "{props.event.source.text}"
        </Typography>
        <Typography variant={"body1"} sx={citationSX}>
          -- {props.event.source.title} ({props.event.source.author})
        </Typography>
      </CardContent>
    </Card>
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
