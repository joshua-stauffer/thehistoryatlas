import { readHistory, navigateHistoryBack, navigateHistoryForward } from "../../hooks/history"
import { NavBar, NavButton, FocusHeader } from "./style"
import { useHistory } from 'react-router-dom';
import { BiTimeFive } from 'react-icons/bi';
import { GoPerson } from 'react-icons/go';
import { VscLocation } from 'react-icons/vsc';

interface HistoryNavBarProps {
  resetCurrentEvents: () => void;
}

export const HistoryNavBar = ({resetCurrentEvents}: HistoryNavBarProps) => {
  const { currentEntity, lastEntity, nextEntity } = readHistory()
  const history = useHistory();
  if (!currentEntity) history.push('/search')
  if (!currentEntity) throw new Error()
  const navigateBack = () => {
    resetCurrentEvents();
    navigateHistoryBack();
  }
  const navigateForward = () => {
    resetCurrentEvents();
    navigateHistoryForward();
  }
  const Icon = currentEntity.entity.type === 'PERSON' 
    ? <GoPerson />
    : currentEntity.entity.type === 'PLACE' 
    ? <VscLocation />
    : <BiTimeFive />

  return (
    <NavBar>
      <NavButton
        onClick={navigateBack}
      >
        Back {lastEntity ? '( ' + lastEntity.entity.name + ' )' : ''}
      </NavButton>
      <FocusHeader>{Icon} {currentEntity.entity.name}</FocusHeader>
      <NavButton
        onClick={navigateForward}
      >
        Forward  {nextEntity ? '( ' + nextEntity.entity.name + ' )' : ''}
      </NavButton>
    </NavBar>
  )
}