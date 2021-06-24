import { readHistory, navigateHistoryBack, navigateHistoryForward } from "../../hooks/history"
import { NavBar, NavButton, FocusHeader } from "./style"
import { useHistory } from 'react-router-dom';

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
  return (
    <NavBar>
      <NavButton
        onClick={navigateBack}
      >
        Back {lastEntity ? '( ' + lastEntity.entity.name + ' )' : ''}
      </NavButton>
      <FocusHeader>{currentEntity.entity.name}</FocusHeader>
      <NavButton
        onClick={navigateForward}
      >
        Forward  {nextEntity ? '( ' + nextEntity.entity.name + ' )' : ''}
      </NavButton>
    </NavBar>
  )
}