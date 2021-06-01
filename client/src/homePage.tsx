import { useState } from 'react';
import { SearchBar } from './components/searchBar';

type EntityID = null | string;

export const HomePage = () => {
  const [entityID, setEntityID] = useState<EntityID>(null);

  if (!entityID) {
    // select an entity
    return (
      <SearchBar handleEntityClick={setEntityID}/>
    )
  }
  return (
    <h1>Entity was chosen! {entityID}</h1>
  )
}