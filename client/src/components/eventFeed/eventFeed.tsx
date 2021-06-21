import { Container } from './style';
import { EventFeedItem } from '../eventFeedItem';
import { GetSummariesByGUIDResult } from '../../graphql/getSummariesByGUID';
import { HistoryEntity } from '../../types';

interface EventFeedProps {
  summaryList: GetSummariesByGUIDResult["GetSummariesByGUID"];
  feedRef: React.RefObject<HTMLDivElement>;
  setCurrentEntity: (entity : HistoryEntity) => void;
}

export const EventFeed = (props: EventFeedProps) => {
  const {
    summaryList,
    feedRef,
    setCurrentEntity
  } = props;

  return (
    <Container ref={feedRef}>
      {summaryList.map(summary => <EventFeedItem summary={summary} key={summary.guid} setCurrentEntity={setCurrentEntity}/>)}
    </Container>
  )
}