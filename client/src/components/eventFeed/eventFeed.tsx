import { Container } from './style';
import { EventFeedItem } from '../eventFeedItem';
import { GetSummariesByGUIDResult } from '../../graphql/getSummariesByGUID';

interface EventFeedProps {
  summaryList: GetSummariesByGUIDResult["GetSummariesByGUID"];
  feedRef: React.RefObject<HTMLDivElement>;
}

export const EventFeed = (props: EventFeedProps) => {
  const {
    summaryList,
    feedRef
  } = props;

  return (
    <Container ref={feedRef}>
      {summaryList.map(summary => <EventFeedItem summary={summary} key={summary.guid}/>)}
    </Container>
  )
}