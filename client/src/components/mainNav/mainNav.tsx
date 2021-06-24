import { useHistory } from 'react-router-dom';
import { Nav, Logo } from './style';
import { HistoryEntity } from '../../types';
import { MenuSearch } from '../../components/menuSearch/menuSearch';
import { addToHistory } from '../../hooks/history';

export const MainNav = () => {
  const history = useHistory();
  const handleEntityClick = (entity: HistoryEntity) => {
    addToHistory(entity);
    history.push('/')
  }
  return (
    <Nav>
      <Logo>The History Atlas</Logo>
      <MenuSearch handleEntityClick={handleEntityClick}/>
    </Nav>
  )  
}