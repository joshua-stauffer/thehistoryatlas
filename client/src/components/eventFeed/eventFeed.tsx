import { Container } from './style';
import { EntityType } from '../../types';
import { EventFeedItem } from '../eventFeedItem';
import { GetSummariesByGUIDResult } from '../../graphql/getSummariesByGUID';

interface EventFeedProps {
  // summaryList: GetSummariesByGUIDResult["GetSummaryByGUIDs"];
  summaryList: string[];
  feedRef: React.RefObject<HTMLDivElement>;
}

export const EventFeed = (props: EventFeedProps) => {
  const {
    summaryList,
    feedRef
  } = props;

  return (
    <Container ref={feedRef}>
      {summaryList.map(guid => <EventFeedItem guid={guid} key={guid}/>)}
    </Container>
  )
}