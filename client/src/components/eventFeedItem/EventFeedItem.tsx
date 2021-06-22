import { ReactElement } from 'react';
import { HistoryEntity } from '../../types';
import { SummaryBox, SummaryText, PersonTag, PlaceTag, TimeTag, SummaryHeader } from './style';
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
  },
  index: number;
  setCurrentEntity: (entity: HistoryEntity) => void;
}

interface TagElementProps {
  tagType: string;
  tagText: string;
  tagGUID: string;
}


export const EventFeedItem = ({ summary, setCurrentEntity, index }: EventFeedItemProps) => {
  const { text, tags } = summary;

  const getTagElement = (props: TagElementProps): ReactElement<any, any> => {
    const { tagType, tagText, tagGUID } = props;
    switch (tagType) {
  
      case 'TIME':
        const prettifiedTime = prettifyDate({ dateString: tagText })
        return <TimeTag onClick={() => setCurrentEntity({ 
          entity: {
            type: "TIME",
            guid: tagGUID
          }
        })}><BiTimeFive /> {prettifiedTime}</TimeTag>
  
      case 'PERSON':
        return <PersonTag onClick={() => setCurrentEntity({
          entity: {
            type: 'PERSON',
            guid: tagGUID
          }
        })}><GoPerson /> {tagText}</PersonTag>
  
      case "PLACE":
        return <PlaceTag onClick={() => setCurrentEntity({
          entity: {
            type: 'PLACE',
            guid: tagGUID
          }
        })}><VscLocation /> {tagText}</PlaceTag>
  
      default: throw new Error('Unknown tag type passed to getTagAndIcon')
    }
  }

  // add tags to text
  const textArray = []; // TODO: add better typing here
  let pointer = 0;
  const sortedTags = tags.slice()
  sortedTags.sort((a, b) => a.start_char - b.start_char)
  for (const tag of sortedTags) {
    const TagElement = getTagElement({
      tagText: text.slice(tag.start_char, tag.stop_char),
      tagType: tag.tag_type,
      tagGUID: tag.tag_guid
    })
    textArray.push(text.slice(pointer, tag.start_char))
    textArray.push(TagElement)
    pointer = tag.stop_char + 1
  }
  textArray.push(text.slice(pointer, text.length))


  return (
    <SummaryBox>
      <SummaryHeader>[ {index} ]</SummaryHeader>
      <SummaryText>
        {textArray}
      </SummaryText>
    </SummaryBox>
  )
}


