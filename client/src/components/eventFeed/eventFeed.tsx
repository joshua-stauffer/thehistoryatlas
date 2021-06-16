import { useRef, useEffect, useLayoutEffect, useState } from 'react';
import { useQuery } from '@apollo/client';
import { Container } from './style';
import { EntityType } from '../../types';
import { EventFeedItem } from '../eventFeedItem';
import { GET_MANIFEST, GetManifestResult, GetManifestVars } from '../../graphql/queries';
import { start } from 'repl';

interface EventFeedProps {
  currentFocusID: string;
  currentFocusType: EntityType;
  lastCitationID?: string;
}

export const EventFeed = (props: EventFeedProps) => {
  // EventFeed constants
  const MAX_START_EVENTS = 20
  const LOAD_ON_SCROLL_COUNT = 20
  const PIXELS_BEFORE_RELOAD = 1000
  const [ newsFeedHasLoaded, setNewsFeedHasLoaded ] = useState<boolean>(false);
  const [ loadedSummaries, setLoadedSummaries ] = useState<Array<string>>([])
  const { currentFocusID, currentFocusType, lastCitationID } = props;
  const { 
    loading: manifestLoading, 
    error: manifestError, 
    data: manifestData 
  } = useQuery<GetManifestResult, GetManifestVars>(
    GET_MANIFEST,
    { variables: { GUID: currentFocusID, entityType: currentFocusType} }
  )

    // create a ref for interacting with the EventFeed container
    const feedEl = useRef<HTMLDivElement>(null)

  // ensure loadedSummaries has the correct initial values
  useEffect(() => {
    if (!manifestData?.GetManifest.citation_guids) return // data isnt loaded yet
    const manifest = manifestData.GetManifest.citation_guids
    if (lastCitationID) {
      const eventsPerSide = Math.ceil(MAX_START_EVENTS / 2)
      // load feed around this guid
      let startIndex = manifest.findIndex((d) => d === lastCitationID)
      if (startIndex === -1) {
        // didn't find the guid, set a reasonable default
        startIndex = 0;
      }
      // try to split initial events evenly on either side of startIndex
      if (manifest.length < MAX_START_EVENTS) {
        // less events than normally loaded at start: load all
        console.log('starting with all events in manifest because there arent enough')
        setLoadedSummaries([...manifest])
      } else if (startIndex < eventsPerSide) {
        console.log('not enough left hand side events')
        // splitting evenly will result in not enough events on the left side
        setLoadedSummaries(manifest.slice(0, MAX_START_EVENTS))
      } else if (startIndex > manifest.length - (eventsPerSide)) {
        console.log('not enough right hand side events')
        // splitting evenly will result in not enough events on the right side
        setLoadedSummaries(manifest.slice(manifest.length - MAX_START_EVENTS, manifest.length))
      } else {
        console.log('we\'re in the middle of the array')
        // we're safely in the middle of the array
        console.log(startIndex - eventsPerSide, startIndex + eventsPerSide)
        setLoadedSummaries(manifest.slice(startIndex - eventsPerSide, startIndex + eventsPerSide))
      }
      setNewsFeedHasLoaded(true)
    }
  }, [manifestData, lastCitationID])

  useLayoutEffect(() => {
    // for now, naively scroll to middle on first render
    if (!feedEl.current) return
    if (!newsFeedHasLoaded) return
    if (!lastCitationID) return
    console.log('jumping to the middle of the feed')
    feedEl.current.scrollTo(0, feedEl.current.scrollHeight / 2)
  }, [newsFeedHasLoaded, lastCitationID])

  // setup scroll/load more logic
  useLayoutEffect(() => {
    if (!manifestData?.GetManifest.citation_guids) return // data isnt loaded yet
    const manifest = manifestData.GetManifest.citation_guids
    const scrollEffect = () => {
      if (!feedEl.current) return;
      const scrollTop = feedEl.current.scrollTop;
      const scrollHeight = feedEl.current.scrollHeight;
      const offsetHeight = feedEl.current.offsetHeight;
      console.log(`scrollTop: ${scrollTop} scrollHeight: ${scrollHeight} offsetHeight: ${offsetHeight}`)
      // Are we within PIXELS_BEFORE_RELOAD of the beginning?
      if (scrollTop < PIXELS_BEFORE_RELOAD) {
        // remember where we are in the feed
        console.log('need to get more data from the beginning')
        const lastPos = scrollTop
        const lastHeight = scrollHeight
        // add elements to beginning
        setLoadedSummaries((curList) => {
          if (curList.length === manifest.length) return curList
          console.log('current list start is ', curList[0])
          const curStartIndex = manifest.findIndex((d) => d === curList[0]);
          console.log('current start index is ', curStartIndex)
          const endIndex = curStartIndex + curList.length;
          let startIndex;
          if (curStartIndex < LOAD_ON_SCROLL_COUNT) {
            startIndex = 0
          } else {
            startIndex = curStartIndex - LOAD_ON_SCROLL_COUNT
          }
          console.log(`list now goes from ${startIndex} to ${endIndex}`)
          return manifest.slice(startIndex, endIndex)
        })
        // ensure that we are scrolled to the same location as before the add
        const newHeight = feedEl.current.scrollHeight;
        const scrollOffset = newHeight - lastHeight;
        // feedEl.current.scrollTo(0, lastPos + scrollOffset)
      } else if ((scrollTop + offsetHeight) > (scrollHeight - PIXELS_BEFORE_RELOAD)) {
        // Are we within PIXELS_BEFORE_RELOAD pixels of the end?
        // add elements to end
        console.log('Need to get more data from the end')
        setLoadedSummaries((curList) => {
          if (curList.length === manifest.length) return curList
          const startIndex = manifest.findIndex((d) => d === curList[0]);
          const curEndIndex = startIndex + curList.length - 1;
          const endIndex = curEndIndex + LOAD_ON_SCROLL_COUNT
          console.log(`list now goes from ${startIndex} to ${endIndex}`)
          return curList.slice(startIndex, endIndex)
        })
        // no need to adjust position, because we're adding to the end
      }
    }
    // add the above function to our window
    window.addEventListener('scroll', scrollEffect, true)
    return () => window.removeEventListener('scroll', scrollEffect, true)
  })

  // make a call to the server to load summaries
  // implement here

  if (manifestLoading) return <h1>...loading manifest</h1>
  if (manifestError) {
    console.log(manifestError)
    return <h1>Error in loading manifest!</h1>
  }
  if (!manifestData) throw new Error('Data was not defined')
  // console.log(manifestData.GetManifest.citation_guids)

  // loadedSummaries logic


  
  return (
    <Container ref={feedEl}>
      {loadedSummaries.map(guid => <EventFeedItem guid={guid} key={guid}/>)}
    </Container>
  )
}

/*

temp0
<div class="sc-bqGGPW bXSYvJ">

temp0.scrollTop
425
allow pasting
Uncaught SyntaxError: unexpected token: identifier
debugger eval code:1:6
temp0.scrollTop
425
temp0.scrollTop / temp0.scrollTopMax
0.7741176470588236
temp0.scrollTo(temp0.scrollTop/2)
Uncaught TypeError: Element.scrollTo: Value can't be converted to a dictionary.
    <anonymous> debugger eval code:1
debugger eval code:1:7
The development server has disconnected.
Refresh the page if necessary. webpackHotDevClient.js:76
temp0.scrollTo(0, temp0.scrollTop/2)
undefined
temp0.scrollTo(0, 0)
undefined
temp0.scrollTo(0, scrollTopMax/2)
Uncaught ReferenceError: scrollTopMax is not defined
    <anonymous> debugger eval code:1
debugger eval code:1:1
temp0.scrollTo(0, temp0.scrollTopMax/2)
undefined

*/