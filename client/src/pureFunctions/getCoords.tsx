import { GetSummariesByGUIDResult } from "../graphql/getSummariesByGUID";
import { MarkerData } from "../types";

interface GetCoordsProps {
  indices: number[];
  currentSummaries: GetSummariesByGUIDResult["GetSummariesByGUID"];
}

interface GetCoordsResult {
  markerData: MarkerData[];
}

export const getCoords = (props: GetCoordsProps): GetCoordsResult => {
  const { indices, currentSummaries } = props;
  const markerData: MarkerData[] = [];
  for (const index of indices) {
    const event = currentSummaries[index];
    if (event) {
      for (const tag of event.tags) {
        if (tag.tag_type === "PLACE") {
          markerData.push({
            coords: [tag.coords.latitude, tag.coords.longitude],
            text: tag.names[0],
            guid: tag.tag_guid,
            coordsObj: {
              latitude: tag.coords.latitude,
              longitude: tag.coords.longitude,
            },
          });
        }
      }
    }
  }
  return {
    markerData: markerData,
  };
};
