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
import {
  HistoryEvent,
  Focus,
  Tag,
  EventPointer,
  Story,
} from "../../graphql/events";
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
import Hidden from "@mui/material/Hidden";
import { SingleEntityMap } from "../../components/singleEntityMap";

interface EventViewProps {
  event: HistoryEvent;
}

const cardSpacingInternal = "5px";

const citationSX = {
  fontSize: "12px",
};

export const EventView = ({ event }: EventViewProps) => {
  return (
    <>
      <Typography textAlign={"center"}>{renderDateTime(event.date)}</Typography>
      <Typography
        variant={"body1"}
        textAlign="left"
        mt={"20px"}
        sx={{
          marginTop: cardSpacingInternal,
          marginBottom: cardSpacingInternal,
        }}
      >
        {buildTaggedText(event)}
      </Typography>

      <Typography variant={"body1"} mt={"20px"} sx={citationSX}>
        "{event.source.text}"
      </Typography>
      <Typography variant={"body1"} sx={citationSX}>
        -- {event.source.title} ({event.source.author})
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
      {event.stories.map((story) => (
        <>
          <Link to={`/stories/${story.id}/events/${event.id}`}>
            <Button sx={{ textTransform: "none" }}>{story.name}</Button>
          </Link>
          <br />
        </>
      ))}
    </>
  );
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
