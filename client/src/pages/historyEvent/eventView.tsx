import React from "react";
import { Button, Typography } from "@mui/material";

import { HistoryEvent, Tag } from "../../graphql/events";
import { renderDateTime } from "../../components/renderDateTime/time";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { BiTimeFive } from "react-icons/bi";
import { TextButton } from "./buttons";
import { Link } from "react-router-dom";

import Divider from "@mui/material/Divider";

interface EventViewProps {
  event: HistoryEvent;
}

const cardSpacingInternal = "5px";

const citationSX = {
  fontSize: "12px", marginLeft: "20px",
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
        Source: {event.source.title}
      </Typography>
      <Typography variant={"body1"} sx={citationSX}>
        Accessed on: {renderDateTime({datetime: event.source.pubDate, precision: 11, calendar: ""})}
      </Typography>
    <Typography variant={"body1"} sx={citationSX}>
        Authors: {event.source.author}
    </Typography>
      <Divider
        sx={{
          marginTop: "20px",
          marginBottom: "20px",
        }}
      />
      {/*<Typography variant={"body2"} fontSize={"18px"} marginLeft={"20px"}>*/}
      {/*  Other stories with this event*/}
      {/*</Typography>*/}
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
