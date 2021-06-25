import { useState, useRef, useLayoutEffect, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { useHistory } from 'react-router';
import {  FeedAndMap, NavAndTimeline } from './style';
import { EventFeed } from '../../components/eventFeed';
import { MapView } from '../../components/map';
import { HistoryNavBar } from '../../components/historyNavigation';
import { BarTimeline } from '../../components/barTimeline';
import { handleFeedScroll } from '../../pureFunctions/scrollLogic';
import { sliceManifest } from '../../pureFunctions/sliceManifest';
import { initManifestSubset } from '../../pureFunctions/initializeManifestSubset';
import { paginateFeed } from '../../pureFunctions/paginateFeed';
import { 
  GET_MANIFEST, GetManifestResult, GetManifestVars,
  GET_SUMMARIES_BY_GUID, GetSummariesByGUIDResult, GetSummariesByGUIDVars
} from '../../graphql/queries';
import { readHistory, addToHistory, addToHistoryProps, updateRootSummary } from '../../hooks/history';
import { MarkerData, FocusedGeoEntity, CurrentFocus } from '../../types';
import { getCoords } from '../../pureFunctions/getCoords';
import { getFocusedGeoData } from '../../pureFunctions/getFocusedGeoData';

interface HomePageProps {

}

export const HomePage = (props: HomePageProps) => {
  // state
  const [ currentEvents, setCurrentEvents ] = useState<string[]>([])
  const [ currentSummaries, setCurrentSummaries ] = useState<GetSummariesByGUIDResult["GetSummariesByGUID"]>([])
  const [ currentCoords, setCurrentCoords ] = useState<MarkerData[]>([])
  const [ focusedGeoEntities, setFocusedGeoEntities] = useState<FocusedGeoEntity[]>([])
  const [ currentFocus, setCurrentFocus ] = useState<CurrentFocus>({
    focusedGUID: 'not a guid',
    scrollIntoView: false
  })


  // hooks & utility functions for state
  const { currentEntity } = readHistory()
  const history = useHistory();
  if (!currentEntity) history.push('/search')
  // add a little check for TypeScript's sake..
  if (!currentEntity) throw new Error()

  // create an onClick handler for navigating between entities
  const setCurrentEntity = (props: addToHistoryProps): void => {
    const { entity, lastSummaryGUID } = props;
    setCurrentEvents([])
    addToHistory( { entity, lastSummaryGUID } )
    if (lastSummaryGUID) {
      setCurrentFocus(currentFocus => {
        return {
          ...currentFocus,
          focusedGUID: lastSummaryGUID,
          scrollIntoView: true
        }
      })
    }
  }
  const resetCurrentEvents = () => setCurrentEvents([]);

  // create an onClick handler for the timeline
  const handleTimelineClick = (guid: string) => {
    updateRootSummary(guid)
    setCurrentEvents([])
  }

  // API Calls
  //  -- load manifest on current entity
  const {
    loading: manifestLoading, 
    error: manifestError, 
    data: manifestData 
  } = useQuery<GetManifestResult, GetManifestVars>(
    GET_MANIFEST,
    { variables: { GUID: currentEntity.entity.guid, entityType: currentEntity.entity.type} }
  )
  //  -- load summaries for slice of manifest currently in event feed
  const {
    loading: summariesLoading,
    data: summariesData 
  } = useQuery<GetSummariesByGUIDResult, GetSummariesByGUIDVars>(
      GET_SUMMARIES_BY_GUID,
      { variables: { summary_guids: currentEvents } }
  )

  // create a ref for interacting with event feed
  const feedRef = useRef<HTMLDivElement>(null)

  // This effect is called when summariesData changes.
  // If data is present, it updates currentSummaries, and updates a flag  
  // to request that the currently focused element scrolls into view.
  useEffect(() => {
    if (!summariesData) return;
    setCurrentSummaries(summariesData.GetSummariesByGUID)
    setCurrentFocus(currentFocus => {
      return {
        ...currentFocus,
        scrollIntoView: true
      }
    })
  }, [summariesData])

  useEffect(() => {
    if (!feedRef.current) return;
    if (!currentSummaries) return;
    const indicesInCurrentPage = paginateFeed({
      elementHeight: 220,
      listLength: currentEvents.length,
      offsetHeight: feedRef.current.offsetHeight,
      scrollHeight: feedRef.current.scrollHeight,
      scrollTop: feedRef.current.scrollTop
    })
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
      const manifestSubset = initManifestSubset({
        eventCount: 20,
        manifest: manifestData.GetManifest.citation_guids,
        rootCitation: currentEntity.rootEventID
      })
      return manifestSubset
    })
  }

  // create a event handler for scroll events
  const handleScroll = (): void => {
    if (!feedRef.current) return;
    if (!manifestData) return;
    if (summariesLoading) return;
    // calculate and set the active summary
    const focusPixel = feedRef.current.scrollTop;
    const focusPercent = focusPixel / feedRef.current.scrollHeight;
    const focusIndex = Math.ceil(focusPercent * (currentSummaries.length))
    setCurrentFocus({
      focusedGUID: currentSummaries[focusIndex].guid,
      scrollIntoView: false
    })
    // calculate if more data should be loaded from either end
    const handleScrollResult = handleFeedScroll({
      pixelsBeforeReload: 1000,
      offsetHeight: feedRef.current.offsetHeight,
      scrollHeight: feedRef.current.scrollHeight,
      scrollTop: feedRef.current.scrollTop
    })
    // update current events with the results of the scroll calculations
    setCurrentEvents(curEvents => {
      return sliceManifest({
        manifest: manifestData.GetManifest.citation_guids,
        manifestSubset: curEvents,
        handleScrollResult: handleScrollResult,
        loadCount: 20
      })
    })
    // find indices for summaries on this data page (events in view plus one view on either side)
    const indicesInCurrentPage = paginateFeed({
      elementHeight: 220,
      listLength: currentEvents.length,
      offsetHeight: feedRef.current.offsetHeight,
      scrollHeight: feedRef.current.scrollHeight,
      scrollTop: feedRef.current.scrollTop
    })
    // create the state for any markers in this data page
    const { markerData } = getCoords({
      indices: indicesInCurrentPage,
      currentSummaries: currentSummaries
     })
     setCurrentCoords(markerData)
     const focusedGeoEntities = getFocusedGeoData({
       currentSummaries: currentSummaries,
       focusIndex: focusIndex
     })
     setFocusedGeoEntities(focusedGeoEntities);
  }

  // add handleScroll to the dom as an event listener
  useLayoutEffect(() => {
    window.addEventListener('scroll', handleScroll, true)
    return () => window.removeEventListener('scroll', handleScroll, true)
  })

  // get the date from our currently focused summary
  let currentDate: string | null = null;
  if (currentSummaries.length) {
    const focusedSummary = currentSummaries.find(summary => summary.guid === currentFocus.focusedGUID);
    if (focusedSummary) {
      // take the first time tag for now
      const timeTag = focusedSummary.tags.find(tag => tag.tag_type === 'TIME');
      currentDate = timeTag && timeTag.name ? timeTag.name : null;
      console.log('current date is ', currentDate)
    }
  }

  return (
      <>
      <NavAndTimeline>
        <BarTimeline
          data={manifestData ? manifestData.GetManifest.timeline : []}
          currentDate={currentDate}
          handleTimelineClick={handleTimelineClick}
        />
        <HistoryNavBar resetCurrentEvents={resetCurrentEvents}/>
      </NavAndTimeline>
      <FeedAndMap>
        <EventFeed 
          summaryList={(!manifestLoading && !manifestError) ? currentSummaries : []}
          eventManifest={manifestData ? manifestData.GetManifest.citation_guids : []}
          feedRef={feedRef}
          setCurrentEntity={setCurrentEntity}
          currentFocus={currentFocus}
        />
        <MapView 
          markers={currentCoords}
          focusedGeoEntities={focusedGeoEntities}
        />
      </FeedAndMap>
      </>
  )
}
