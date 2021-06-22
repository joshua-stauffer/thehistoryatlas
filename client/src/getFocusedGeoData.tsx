import { GetSummariesByGUIDResult } from './graphql/getSummariesByGUID';
import { FocusedGeoEntity } from './types';

interface GetFocusedGeoDataProps {
  currentSummaries: GetSummariesByGUIDResult["GetSummariesByGUID"];
  focusIndex: number;
}

export const getFocusedGeoData = (props: GetFocusedGeoDataProps): FocusedGeoEntity[] => {
  const { focusIndex, currentSummaries } = props;
  const summary = currentSummaries[focusIndex];
  if (!summary) throw new Error('Out of range focusIndex was passed to getFocusedGUIDs.')
  const focusedEntities: FocusedGeoEntity[] = []
  for (const tag of summary.tags) {
    if (tag.tag_type === 'PLACE' && tag.coords) {
      focusedEntities.push({
        GUID: tag.tag_guid,
        coords: {
          latitude: tag.coords.latitude,
          longitude: tag.coords.longitude
        }
      })
    }
  }
  return focusedEntities
}