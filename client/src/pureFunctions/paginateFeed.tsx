
interface paginateFeedProps {
  scrollTop: number;
  offsetHeight: number;
  scrollHeight: number;
  listLength: number;
  elementHeight: number;
}
type indicesOnDataPage = number[];

export const paginateFeed = (props: paginateFeedProps): indicesOnDataPage => {
  const {
    scrollTop, 
    offsetHeight, 
    scrollHeight, 
    listLength, 
    elementHeight, 
  } = props;
  const topPercent = scrollTop / scrollHeight;
  const firstIndex = Math.ceil(topPercent * listLength);
  const elementsInView = Math.floor(offsetHeight / elementHeight);

  // find which indices are on the current page of data?
  let indicesOnPage;
  const elementsInPage = elementsInView * 3;
  const edgeIndex = elementsInView * 2;
  if (elementsInPage > listLength) {
    // return all indices
    indicesOnPage = Array.from({ length: listLength }).map((_, i) => i);
  } else if (firstIndex < edgeIndex) {
    // we're close to the beginning, return a full page from the beginning
    indicesOnPage = Array.from({ length: elementsInPage }).map((_, i) => i);
  } else if ((listLength - firstIndex) < edgeIndex) {
    // we're close to the end, a full page from the end
    const startI = listLength - elementsInPage;
    indicesOnPage =  Array.from({ length: elementsInPage }).map((_, i) => i + startI)
  } else {
    // we're in the middle, return a page
    const pageOffset = firstIndex % elementsInView;
    const startI = firstIndex - pageOffset - elementsInView;
    indicesOnPage =  Array.from({ length: elementsInPage }).map((_, i) => i + startI)
  }

  return indicesOnPage
}