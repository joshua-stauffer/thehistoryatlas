import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Collapse,
  IconButton,
  CardHeader,
  TextField,
  Chip,
  Button,
} from "@mui/material";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { EventItem, Focus, Tag } from "../../graphql/events";
import { Box } from "@material-ui/core";
import { renderDateTime } from "../../components/renderDateTime/time";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { BiTimeFive } from "react-icons/bi";
import SearchIcon from "@mui/icons-material/Search";
interface NewFeedCardProps {
  event: EventItem;
  openTimeTravelModal: () => void;
}

export const NewFeedCard = (props: NewFeedCardProps) => {
  return (
    <Card sx={{}}>
      <CardHeader
        sx={{ textAlign: "center" }}
        title={buildCurrentFocus(props.event.focus)}
        subheader={renderDateTime(props.event.date)}
      />
      <CardActions disableSpacing>
        <IconButton sx={{ marginLeft: "auto", marginRight: "auto" }}>
          <ArrowBackIcon />
        </IconButton>
        <Button onClick={props.openTimeTravelModal}>
          <SearchIcon />
          Jump To Time
        </Button>
        <IconButton sx={{ marginLeft: "auto", marginRight: "auto" }}>
          <ArrowForwardIcon />
        </IconButton>
      </CardActions>

      <CardContent>
        <Typography
          paragraph
          gutterBottom
          textAlign="center"
          sx={{
            marginTop: 8,
            marginBottom: 8,
          }}
        >
          {buildTaggedText(props.event)}
        </Typography>
      </CardContent>
      <CardContent sx={{ marginLeft: "40px", marginRight: "40px" }}>
        <Typography paragraph>"{props.event.source.text}"</Typography>
        <Typography paragraph>
          -- {props.event.source.title} ({props.event.source.author})
        </Typography>
      </CardContent>
    </Card>
  );
};

const buildCurrentFocus = (focus: Focus | null) => {
  if (!focus) {
    return "The history of the world";
  } else if (focus.type === "PERSON") {
    return `The life of ${focus.name}`;
  } else {
    return `The history of ${focus.name}`;
  }
};

const buildTaggedText = (event: EventItem): (string | JSX.Element | null)[] => {
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
      return (
        <Button>
          {tag.name} {icon}
        </Button>
      );
    } else if (tagIndicesSet.has(index)) {
      return null;
    } else {
      return char;
    }
  });
};
