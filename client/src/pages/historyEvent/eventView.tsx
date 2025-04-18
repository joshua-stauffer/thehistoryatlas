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
  fontSize: "12px",
  marginLeft: "20px",
};

export const EventView = ({ event }: EventViewProps) => {
  return (
    <>
      <Typography textAlign={"center"}>{renderDateTime(event.date)}</Typography>
      <Typography
        variant={"body1"}
        textAlign="left"
        mt={"20px"}
        component="p"
        role="paragraph"
        sx={{
          marginTop: cardSpacingInternal,
          marginBottom: cardSpacingInternal,
          width: "calc(100% - 48px)",
          margin: "0 24px",
          overflowWrap: "break-word",
          wordWrap: "break-word",
          hyphens: "auto",
          position: "relative",
          left: 0,
          maxWidth: "100%",
          boxSizing: "border-box",
          padding: "24px 32px",
          fontSize: "1.25rem",
          lineHeight: 1.8,
          color: "#2C3E50",
          letterSpacing: "0.01em",
          backgroundColor: "#FAFBFC",
          borderRadius: "8px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          border: "1px solid rgba(0,0,0,0.05)",
        }}
      >
        {buildTaggedText(event)}
      </Typography>

      <Typography variant={"body1"} mt={"20px"} sx={citationSX}>
        Source: {event.source.title}
      </Typography>
      <Typography variant={"body1"} sx={citationSX}>
        Accessed on:{" "}
        {new Date(event.source.pubDate).toLocaleDateString("en-US", {
          weekday: "long",
          year: "numeric",
          month: "long",
          day: "numeric",
        })}
      </Typography>
      <Typography variant={"body1"} sx={citationSX}>
        Authors: {event.source.author}
      </Typography>

      {/*<Typography variant={"body2"} fontSize={"18px"} marginLeft={"20px"}>*/}
      {/*  Other stories with this event*/}
      {/*</Typography>*/}
      {event.stories.map((story) => (
        <div key={story.id}>
          <Link to={`/stories/${story.id}/events/${event.id}`}>
            <Button sx={{ textTransform: "none" }}>{story.name}</Button>
          </Link>
          <br />
        </div>
      ))}
    </>
  );
};

const buildTaggedText = (
  event: HistoryEvent,
): (string | JSX.Element | null)[] => {
  let tagIndices: Array<number> = [];
  for (const tag of event.tags) {
    const indices = Array.from(
      { length: tag.stopChar - tag.startChar },
      (_, i) => tag.startChar + i,
    );
    tagIndices = [...tagIndices, ...indices];
  }
  const tagIndicesSet = new Set(tagIndices);
  const startCharMap: Map<number, Tag> = new Map(
    event.tags.map((tag) => [tag.startChar, tag]),
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
        <Link
          key={`${tag.id}-${index}`}
          to={storyUrl}
          style={{ textDecoration: "none" }}
        >
          <TextButton text={tag.name} />
        </Link>
      );
    } else if (tagIndicesSet.has(index)) {
      return null;
    } else {
      return char;
    }
  });
};
