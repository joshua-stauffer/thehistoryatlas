import { useState } from 'react';
import { SearchBar } from './components/searchBar';
import { EventFeed } from './components/eventFeed';
import { EntityType } from './types';

export type CurrentEntity = null | Entity;

interface Entity {
  guid: string;
  type: EntityType;
}

export const HomePage = () => {
  const [currentEntity, setCurrentEntity] = useState<CurrentEntity>(null);

  if (!currentEntity) {
    // select an entity
    return (
      <SearchBar handleEntityClick={setCurrentEntity}/>
    )
  }
  return (
    <EventFeed 
      currentFocusID={currentEntity.guid}
      currentFocusType={currentEntity.type}
      lastCitationID={"a28adc11-5ccb-4a32-9fa0-c01ddf447c54"}
    />
  )
}