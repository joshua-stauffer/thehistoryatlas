interface initManifestSubsetProps {
  manifest: string[];
  eventCount: number;
  rootCitation?: string;
}

export const initManifestSubset = (
  props: initManifestSubsetProps
): string[] => {
  const { manifest, eventCount, rootCitation } = props;
  // base no-compute cases
  if (manifest.length < eventCount) {
    return manifest.slice();
  }
  if (!rootCitation) {
    return manifest.slice(0, eventCount);
  }
  // compute logic
  const rootIndex = manifest.findIndex((guid) => guid === rootCitation);
  const oneSideCount = Math.ceil(eventCount / 2);
  // edge cases:
  if (rootIndex < 0) {
    // didn't find root citation, fallback to reasonable default
    return manifest.slice(0, eventCount);
  }
  if (rootIndex <= oneSideCount) {
    // citation is in the first x, but we want to load eventCount events anyways.
    return manifest.slice(0, eventCount);
  }
  if (rootIndex >= manifest.length - oneSideCount) {
    // citation is in the last x, but we want to load eventCount events anyways.
    return manifest.slice(manifest.length - eventCount);
  }
  // primary logic
  return manifest.slice(rootIndex - oneSideCount, rootIndex + oneSideCount);
};
