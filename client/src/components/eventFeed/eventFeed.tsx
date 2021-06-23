import { CurrentFocus } from '../../types';
import { Container } from './style';
import { EventFeedItem } from '../eventFeedItem';
import { GetSummariesByGUIDResult } from '../../graphql/getSummariesByGUID';
import { addToHistoryProps } from '../../hooks/history';

interface EventFeedProps {
  summaryList: GetSummariesByGUIDResult["GetSummariesByGUID"];
  feedRef: React.RefObject<HTMLDivElement>;
  setCurrentEntity: (props : addToHistoryProps) => void;
  eventManifest: string[];
  currentFocus: CurrentFocus;
}

export const EventFeed = (props: EventFeedProps) => {
  const {
    summaryList,
    feedRef,
    setCurrentEntity,
    eventManifest,
    currentFocus
  } = props;
  const manifestMap = new Map<string, number>()
  for (let i = 0; i < eventManifest.length; i++) {
    manifestMap.set(eventManifest[i], i)
  }
  

  return (
    <Container ref={feedRef}>
      {summaryList.map((summary, i) => 
        <EventFeedItem summary={summary} 
          index={manifestMap.get(summary.guid)} 
          key={i} 
          setCurrentEntity={setCurrentEntity}
          currentFocus={currentFocus}
        />)}
    </Container>
  )
}