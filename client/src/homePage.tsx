import { useState, useRef, useLayoutEffect } from 'react';
import { useQuery } from '@apollo/client';
import { SearchBar } from './components/searchBar';
import { EventFeed } from './components/eventFeed';
import { EntityType } from './types';
import { handleFeedScroll } from './scrollLogic';
import { sliceManifest } from './sliceManifest';
import { initManifestSubset } from './initializeManifestSubset';
import { GET_MANIFEST, GetManifestResult, GetManifestVars } from './graphql/queries';


export type CurrentEntity = null | Entity;

export interface Entity {
  guid: string;
  type: EntityType;
}

export interface EntityHistory {
  entity: Entity;
  rootEventID?: string;
}

export const HomePage = () => {
  
  // history logic
  const [entityHistory, setEntityHistory] = useState<EntityHistory[]>([{
    // TODO: pass this in as props
    entity: {
      guid: 'bd025284-890b-42c5-88a7-27f417737955',
      type: 'PERSON',
    },
    rootEventID: 'b947ffcd-a7e6-490c-ad65-e969642f9bb7'
  }]);
  const setCurrentEntity = (entry: EntityHistory): void => {
    setEntityHistory(history => [...history, entry])
  }
  const { entity: currentEntity, rootEventID } = entityHistory[entityHistory.length - 1]
  // track events currently in feed
  const [ currentEvents, setCurrentEvents ] = useState<string[] | null>(null)

  // load manifest on current entity
  const { 
    loading: manifestLoading, 
    error: manifestError, 
    data: manifestData 
  } = useQuery<GetManifestResult, GetManifestVars>(
    GET_MANIFEST,
    { variables: { GUID: currentEntity.guid, entityType: currentEntity.type} }
  )

  const feedRef = useRef<HTMLDivElement>(null)

  // feed logic
  // has the feed been initialized?
  if (!currentEvents && manifestData) {
    setCurrentEvents(curEvents => {
      return initManifestSubset({
        eventCount: 20,
        manifest: manifestData.GetManifest.citation_guids,
        rootCitation: rootEventID
      })
    })
  }
  // create a event handler for scroll events
  const handleScroll = (): void => {
    if (!feedRef.current) return;
    if (!manifestData) return;
    const handleScrollResult = handleFeedScroll({
      pixelsBeforeReload: 1000,
      offsetHeight: feedRef.current.offsetHeight,
      scrollHeight: feedRef.current.scrollHeight,
      scrollTop: feedRef.current.scrollTop
    })
    setCurrentEvents(curEvents => {
      if (!curEvents) return null;
      return sliceManifest({
        manifest: manifestData.GetManifest.citation_guids,
        manifestSubset: curEvents,
        handleScrollResult: handleScrollResult,
        loadCount: 20
      })
    })
  }
  
  useLayoutEffect(() => {
    window.addEventListener('scroll', handleScroll, true)
    return () => window.removeEventListener('scroll', handleScroll, true)
  })

  // if no entity has been selected yet, show a search page
  if (!currentEntity) {
    // select an entity
    return (
      <SearchBar handleEntityClick={setCurrentEntity}/>
    )
  }

  // manifest is loading, or there was an error
  if (manifestLoading) return <h1>...loading manifest</h1>
  if (manifestError) {
    console.log(manifestError)
    return <h1>Error in loading manifest!</h1>
  }
  if (!currentEvents) {
    return <h1>Current Events havent loaded.</h1>
  }

  return (
    <EventFeed 
      summaryList={currentEvents}
      feedRef={feedRef}
    />
  )
}