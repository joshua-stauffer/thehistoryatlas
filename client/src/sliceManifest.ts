import { handleScrollResult } from './scrollLogic';

interface sliceManifestProps {
  manifest: string[];
  manifestSubset: string[];
  loadCount: number;
  handleScrollResult: handleScrollResult;
}


export const sliceManifest = (props: sliceManifestProps): string[] => {
  // transform manifest based on handleScrollResult object
  const {
    manifest,
    manifestSubset,
    loadCount,
    handleScrollResult
  } = props;
  const { loadFromBeginning, loadFromEnd } = handleScrollResult;
  // base case -- no need to calculate anything
  if (manifest.length === manifestSubset.length) return manifestSubset;
  // primary logic to extend list in either direction
  if (loadFromBeginning) {
    const curStartIndex = manifest.findIndex((d) => d === manifestSubset[0]);
    const startIndex = curStartIndex - loadCount >= 0
      ? curStartIndex - loadCount
      : 0
    const endIndex = curStartIndex + manifestSubset.length
    return manifest.slice(startIndex, endIndex)
  } else if (loadFromEnd) {
    const startIndex = manifest.findIndex((d) => d === manifestSubset[0]);
    const endIndex = startIndex + manifestSubset.length + loadCount;
    return manifest.slice(startIndex, endIndex)
  }
  // no reload was requested, return the subset as is
  return manifestSubset
}
