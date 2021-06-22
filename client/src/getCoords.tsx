import { GetSummariesByGUIDResult } from './graphql/getSummariesByGUID';
import { MarkerData } from './types';

interface GetCoordsProps {
  indices: number[];
  currentSummaries: GetSummariesByGUIDResult["GetSummariesByGUID"];
}

interface GetCoordsResult {
  markerData: MarkerData[]
}

export const getCoords = (props: GetCoordsProps ): GetCoordsResult => {
  const { indices, currentSummaries } = props;
  const markerData: MarkerData[] = [];
  for (const index of indices) {
    const event = currentSummaries[index]
    if (event) {
      const placeTags = event.tags.filter(tag => tag.tag_type === 'PLACE')
      for (const tag of placeTags) {
        if (tag.coords && tag.names) {
          markerData.push({
            coords: [tag.coords.latitude, tag.coords.longitude],
            text: tag.names[0],
            guid: tag.tag_guid
          })
        }
      }
    }

  }
  return {
    markerData: markerData
  }
}