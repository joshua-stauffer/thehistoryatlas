

interface handleScrollProps {
  scrollTop: number;
  scrollHeight: number;
  offsetHeight: number;
  pixelsBeforeReload: number;
}

export interface handleScrollResult {
  loadFromBeginning: boolean;
  loadFromEnd: boolean;
}

export const handleFeedScroll = (props: handleScrollProps): handleScrollResult => {
  // calculate if we've scrolled into reload territory
  const {
    scrollTop,
    scrollHeight,
    offsetHeight,
    pixelsBeforeReload
  } = props;
  if (scrollTop < pixelsBeforeReload) {
    return {
      loadFromBeginning: true,
      loadFromEnd: false
    }
  } else if ((scrollTop + offsetHeight) > (scrollHeight - pixelsBeforeReload)) {
    return {
      loadFromBeginning: false,
      loadFromEnd: true
    }
  } else {
    return {
      loadFromBeginning: false,
      loadFromEnd: false
    }
  }
}
