import { Main } from './style';
import { SearchBar } from '../../components/searchBar';
import { addToHistory } from '../../hooks/history';

export const SearchPage = () => {

  return (
    <Main>
      <SearchBar handleEntityClick={addToHistory}/>
    </Main>
  )
}