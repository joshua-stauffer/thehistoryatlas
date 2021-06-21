import { useState, useRef, useLayoutEffect, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { EventFeed } from './components/eventFeed';
import { HistoryNavBar } from './components/historyNavigation';
import { handleFeedScroll } from './scrollLogic';
import { sliceManifest } from './sliceManifest';
import { initManifestSubset } from './initializeManifestSubset';
import { 
  GET_MANIFEST, GetManifestResult, GetManifestVars,
  GET_SUMMARIES_BY_GUID, GetSummariesByGUIDResult, GetSummariesByGUIDVars
} from './graphql/queries';
import { readHistory, addToHistory } from './history';
import { HistoryEntity } from './types';




interface HomePageProps {

}

export const HomePage = (props: HomePageProps) => {
  // track events currently in feed
  const [ currentEvents, setCurrentEvents ] = useState<string[]>([])
  const [ currentSummaries, setCurrentSummaries ] = useState<GetSummariesByGUIDResult["GetSummariesByGUID"]>([])
  const setCurrentEntity = (entity: HistoryEntity): void => {
    setCurrentEvents([])
    addToHistory(entity)
  }
  const resetCurrentEvents = () => setCurrentEvents([]);
  // history logic

  const { currentEntity } = readHistory()

    // load manifest on current entity
  const {
    loading: manifestLoading, 
    error: manifestError, 
    data: manifestData 
  } = useQuery<GetManifestResult, GetManifestVars>(
    GET_MANIFEST,
    { variables: { GUID: currentEntity.entity.guid, entityType: currentEntity.entity.type} }
  )

  // load summaries for slice of manifest currently in event feed
  const {
    loading: summariesLoading,
    data: summariesData 
  } = useQuery<GetSummariesByGUIDResult, GetSummariesByGUIDVars>(
      GET_SUMMARIES_BY_GUID,
      { variables: { summary_guids: currentEvents } }
  )

  // const summariesList = summariesData ? summariesData.GetSummariesByGUID : [];
  useEffect(() => {
    if (!summariesData) return;
    setCurrentSummaries(summariesData.GetSummariesByGUID)
  }, [summariesData])

  const feedRef = useRef<HTMLDivElement>(null)

  // feed logic
  // has the feed been initialized?
  if (!currentEvents.length && manifestData) {
    setCurrentEvents(() => {
      return initManifestSubset({
        eventCount: 20,
        manifest: manifestData.GetManifest.citation_guids,
        rootCitation: currentEntity.rootEventID
      })
    })
  }
  // create a event handler for scroll events
  const handleScroll = (): void => {
    if (!feedRef.current) return;
    if (!manifestData) return;
    if (summariesLoading) return;
    const handleScrollResult = handleFeedScroll({
      pixelsBeforeReload: 1000,
      offsetHeight: feedRef.current.offsetHeight,
      scrollHeight: feedRef.current.scrollHeight,
      scrollTop: feedRef.current.scrollTop
    })
    setCurrentEvents(curEvents => {
      return sliceManifest({
        manifest: manifestData.GetManifest.citation_guids,
        manifestSubset: curEvents,
        handleScrollResult: handleScrollResult,
        loadCount: 20
      })
    }) // else, we're still waiting for the last result
  }

  useLayoutEffect(() => {
    window.addEventListener('scroll', handleScroll, true)
    return () => window.removeEventListener('scroll', handleScroll, true)
  })

  // manifest is loading, or there was an error
  if (manifestLoading) return <h1>...loading manifest</h1>
  if (manifestError) {
    console.log(manifestError)
    return <h1>Error in loading manifest!</h1>
  }

  return (
    <>
    <HistoryNavBar resetCurrentEvents={resetCurrentEvents}/>
    <EventFeed 
      summaryList={currentSummaries}
      feedRef={feedRef}
      setCurrentEntity={setCurrentEntity}
    />
    </>
  )
}