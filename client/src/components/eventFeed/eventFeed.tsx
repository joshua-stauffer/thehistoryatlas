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
      {summaryList.map((summary, i) => <EventFeedItem summary={summary} index={i} key={i} setCurrentEntity={setCurrentEntity}/>)}
    </Container>
  )
}