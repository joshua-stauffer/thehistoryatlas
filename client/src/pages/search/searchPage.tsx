import { SearchBar } from "../../components/searchBar";
import { addToHistory } from "../../hooks/history";
import { HistoryEntity } from "../../types";
import { useHistory } from "react-router";

export const SearchPage = () => {
  const history = useHistory();
  const handleEntityClick = (entity: HistoryEntity) => {
    addToHistory(entity);
    history.push("/");
  };
  return <SearchBar handleEntityClick={handleEntityClick} />;
};
