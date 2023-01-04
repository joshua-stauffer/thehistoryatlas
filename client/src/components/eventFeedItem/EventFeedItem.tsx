import { useRef, ReactElement } from "react";
import { CurrentFocus } from "../../types";
import {
  FocusedSummaryBox,
  FocusedSummaryText,
  FocusedSummaryHeader,
  FocusedPersonTag,
  FocusedPlaceTag,
  FocusedTimeTag,
  SummaryBox,
  SummaryText,
  PersonTag,
  PlaceTag,
  TimeTag,
  SummaryHeader,
} from "./style";
import { prettifyDate } from "../../pureFunctions/prettifyDate";
import { BiTimeFive } from "react-icons/bi";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { addToHistoryProps } from "../../hooks/history";
import { Citation } from "./citation";

interface EventFeedItemProps {
  summary: {
    guid: string;
    text: string;
    tags: {
      tag_type: string;
      tag_guid: string;
      start_char: number;
      stop_char: number;
      names?: string[] | undefined;
      name?: string | undefined;
    }[];
    citation_guids: string[];
  };
  index: number | undefined;
  setCurrentEntity: (props: addToHistoryProps) => void;
  currentFocus: CurrentFocus;
}

export const EventFeedItem = ({
  summary,
  setCurrentEntity,
  index,
  currentFocus,
}: EventFeedItemProps) => {
  const { text, tags, guid: summaryGUID, citation_guids } = summary;
  const ref = useRef<HTMLDivElement>(null);
  const { focusedGUID, scrollIntoView } = currentFocus;
  // add tags to text
  const textArray = []; // TODO: add better typing here
  let pointer = 0;
  const sortedTags = tags.slice();
  sortedTags.sort((a, b) => a.start_char - b.start_char);
  for (const tag of sortedTags) {
    const TagElement = getTagElement({
      tagText: text.slice(tag.start_char, tag.stop_char),
      tagType: tag.tag_type,
      tagGUID: tag.tag_guid,
      name: tag.name,
      names: tag.names,
      setCurrentEntity: setCurrentEntity,
      summaryGUID: summaryGUID,
      isFocused: summaryGUID === focusedGUID,
    });
    textArray.push(text.slice(pointer, tag.start_char));
    textArray.push(TagElement);
    pointer = tag.stop_char + 1;
  }
  textArray.push(text.slice(pointer, text.length));

  // is this the focused event?
  if (ref.current && summaryGUID === focusedGUID) {
    // do we need to scroll?
    if (scrollIntoView) ref.current.scrollIntoView();
    return (
      <FocusedSummaryBox ref={ref}>
        <FocusedSummaryHeader>{index}</FocusedSummaryHeader>
        <FocusedSummaryText>{textArray}</FocusedSummaryText>
        <Citation guid={citation_guids[0]} />
      </FocusedSummaryBox>
    );
  }

  return (
    <SummaryBox ref={ref}>
      <SummaryHeader>{index}</SummaryHeader>
      <SummaryText>{textArray}</SummaryText>
      <Citation guid={citation_guids[0]} />
    </SummaryBox>
  );
};

interface TagElementProps {
  tagType: string;
  tagText: string;
  tagGUID: string;
  name?: string | undefined;
  names?: string[] | undefined;
  setCurrentEntity: (props: addToHistoryProps) => void;
  summaryGUID: string;
  isFocused: boolean;
}

// utility function to generate inline span tags
const getTagElement = (props: TagElementProps): ReactElement<any, any> => {
  const {
    tagType,
    tagText,
    tagGUID,
    setCurrentEntity,
    summaryGUID,
    isFocused,
  } = props;

  switch (tagType) {
    case "TIME": {
      const prettifiedTime = prettifyDate({ dateString: tagText });

      const tag = isFocused ? (
        <FocusedTimeTag
          onClick={() =>
            setCurrentEntity({
              entity: {
                type: "TIME",
                guid: tagGUID,
                name: prettifiedTime ? prettifiedTime : tagText,
              },
              lastSummaryGUID: summaryGUID,
            })
          }
        >
          <BiTimeFive /> {prettifiedTime}
        </FocusedTimeTag>
      ) : (
        <TimeTag
          onClick={() =>
            setCurrentEntity({
              entity: {
                type: "TIME",
                guid: tagGUID,
                name: prettifiedTime ? prettifiedTime : tagText,
              },
              lastSummaryGUID: summaryGUID,
            })
          }
        >
          <BiTimeFive /> {prettifiedTime}
        </TimeTag>
      );
      return tag;
    }

    case "PERSON": {
      const tag = isFocused ? (
        <FocusedPersonTag
          onClick={() =>
            setCurrentEntity({
              entity: {
                type: "PERSON",
                guid: tagGUID,
                name: tagText,
              },
              lastSummaryGUID: summaryGUID,
            })
          }
        >
          <GoPerson /> {tagText}
        </FocusedPersonTag>
      ) : (
        <PersonTag
          onClick={() =>
            setCurrentEntity({
              entity: {
                type: "PERSON",
                guid: tagGUID,
                name: tagText,
              },
              lastSummaryGUID: summaryGUID,
            })
          }
        >
          <GoPerson /> {tagText}
        </PersonTag>
      );
      return tag;
    }

    case "PLACE": {
      const tag = isFocused ? (
        <FocusedPlaceTag
          onClick={() =>
            setCurrentEntity({
              entity: {
                type: "PLACE",
                guid: tagGUID,
                name: tagText,
              },
              lastSummaryGUID: summaryGUID,
            })
          }
        >
          <VscLocation /> {tagText}
        </FocusedPlaceTag>
      ) : (
        <PlaceTag
          onClick={() =>
            setCurrentEntity({
              entity: {
                type: "PLACE",
                guid: tagGUID,
                name: tagText,
              },
              lastSummaryGUID: summaryGUID,
            })
          }
        >
          <VscLocation /> {tagText}
        </PlaceTag>
      );
      return tag;
    }

    default:
      throw new Error("Unknown tag type passed to getTagAndIcon");
  }
};
