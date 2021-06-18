import { ReactElement } from 'react';
import { SummaryBox, SummaryText, PersonTag, PlaceTag, TimeTag } from './style';
import { prettifyDate } from '../../prettifyDate';
import { BiTimeFive } from 'react-icons/bi';
import { GoPerson } from 'react-icons/go';
import { VscLocation } from 'react-icons/vsc';

interface EventFeedItemProps {
  summary: {
    guid: string;
    text: string;
    tags: {
      tag_type: string;
      tag_guid: string;
      start_char: number;
      stop_char: number;
    }[]
  }
}

export const EventFeedItem = ({ summary }: EventFeedItemProps) => {
  const { text, tags } = summary;

  // add tags to text
  const textArray = []; // TODO: add better typing here
  let pointer = 0;
  const sortedTags = tags.slice()
  sortedTags.sort((a, b) => a.start_char - b.start_char)
  for (const tag of sortedTags) {
    const TagElement = getTagElement({
      tagText: text.slice(tag.start_char, tag.stop_char),
      tagType: tag.tag_type
    })
    textArray.push(text.slice(pointer, tag.start_char))
    textArray.push(TagElement)
    pointer = tag.stop_char + 1
  }
  textArray.push(text.slice(pointer, text.length))


  return (
    <SummaryBox>
      <SummaryText>
        {textArray}
      </SummaryText>
    </SummaryBox>
  )
}

interface TagElementProps {
  tagType: string;
  tagText: string;
}

const getTagElement = (props: TagElementProps): ReactElement<any, any> => {
  const { tagType, tagText } = props;
  switch (tagType) {

    case "TIME":
      const prettifiedTime = prettifyDate({ dateString: tagText })
      return <TimeTag><BiTimeFive /> {prettifiedTime}</TimeTag>

    case "PERSON":
      return <PersonTag><GoPerson /> {tagText}</PersonTag>

    case "PLACE":
      return <PlaceTag><VscLocation /> {tagText}</PlaceTag>

    default: throw new Error('Unknown tag type passed to getTagAndIcon')
  }
}