import { useState, useRef, useLayoutEffect, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { Main, FeedAndMap } from './style';
import { EventFeed } from './components/eventFeed';
import { Map } from './components/map';
import { HistoryNavBar } from './components/historyNavigation';
import { handleFeedScroll } from './scrollLogic';
import { sliceManifest } from './sliceManifest';
import { initManifestSubset } from './initializeManifestSubset';
import { paginateFeed } from './paginateFeed';
import { 
  GET_MANIFEST, GetManifestResult, GetManifestVars,
  GET_SUMMARIES_BY_GUID, GetSummariesByGUIDResult, GetSummariesByGUIDVars
} from './graphql/queries';
import { readHistory, addToHistory } from './history';
import { HistoryEntity, MarkerData, FocusedGeoEntity } from './types';
import { getCoords } from './getCoords';
import { getFocusedGeoData } from './getFocusedGeoData';

interface HomePageProps {

}

export const HomePage = (props: HomePageProps) => {
  // track events currently in feed
  const [ currentEvents, setCurrentEvents ] = useState<string[]>([])
  const [ currentSummaries, setCurrentSummaries ] = useState<GetSummariesByGUIDResult["GetSummariesByGUID"]>([])
  const [ currentCoords, setCurrentCoords ] = useState<MarkerData[]>([])
  const [ focusedGeoEntities, setFocusedGeoEntities] = useState<FocusedGeoEntity[]>([])
  const { currentEntity } = readHistory()

  const setCurrentEntity = (entity: HistoryEntity): void => {
    setCurrentEvents([])
    addToHistory(entity)
  }
  const resetCurrentEvents = () => setCurrentEvents([]);

  // API Calls
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

  const feedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!summariesData) return;
    setCurrentSummaries(summariesData.GetSummariesByGUID)
  }, [summariesData])

  useEffect(() => {
    if (!feedRef.current) return;
    if (!currentSummaries)
    console.log('checking feed pagination')
    const {
      indicesInView,
      activeIndex,
      indicesInCurrentPage
    } = paginateFeed({
      elementHeight: 220,
      listLength: currentEvents.length,
      offsetHeight: feedRef.current.offsetHeight,
      scrollHeight: feedRef.current.scrollHeight,
      scrollTop: feedRef.current.scrollTop
    })
    console.log('indices in view: ', indicesInView, ' active index ', activeIndex, ' indices in current page ', indicesInCurrentPage)
    const { markerData } = getCoords({
      indices: indicesInCurrentPage,
      currentSummaries: currentSummaries
     })
     setCurrentCoords(markerData)
  }, [feedRef, currentEvents.length, currentSummaries])


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
    console.log('checking feed pagination')
    const {
      indicesInView,
      activeIndex,
      indicesInCurrentPage
    } = paginateFeed({
      elementHeight: 220,
      listLength: currentEvents.length,
      offsetHeight: feedRef.current.offsetHeight,
      scrollHeight: feedRef.current.scrollHeight,
      scrollTop: feedRef.current.scrollTop
    })
    console.log('indices in view: ', indicesInView, ' active index ', activeIndex, ' indices in current page ', indicesInCurrentPage)
    const { markerData } = getCoords({
      indices: indicesInCurrentPage,
      currentSummaries: currentSummaries
     })
     setCurrentCoords(markerData)
     const focusedGeoEntities = getFocusedGeoData({
       currentSummaries: currentSummaries,
       focusIndex: activeIndex
     })
     setFocusedGeoEntities(focusedGeoEntities);
  }


  useLayoutEffect(() => {
    window.addEventListener('scroll', handleScroll, true)
    return () => window.removeEventListener('scroll', handleScroll, true)
  })
  console.log(focusedGeoEntities)
  const longitude = focusedGeoEntities.length ? focusedGeoEntities[0].coords.longitude : -25; 
  const latitude = focusedGeoEntities.length ? focusedGeoEntities[0].coords.latitude : -25; 

  return (
    <Main>
      <HistoryNavBar resetCurrentEvents={resetCurrentEvents}/>
      <FeedAndMap>

        <EventFeed 
          summaryList={(!manifestLoading && !manifestError) ? currentSummaries : []}
          feedRef={feedRef}
          setCurrentEntity={setCurrentEntity}
        />

        <Map 
          latitude={latitude}
          longitude={longitude}
          zoom={6}
          markers={currentCoords}
          focusedGeoEntities={focusedGeoEntities}
      />

      </FeedAndMap>
      
    </Main>
  )
}
