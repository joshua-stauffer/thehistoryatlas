import { readHistory, navigateHistoryBack, navigateHistoryForward } from "../../hooks/history"
import { NavBar, NavButton, FocusHeader } from "./style"

interface HistoryNavBarProps {
  resetCurrentEvents: () => void;
}

export const HistoryNavBar = ({resetCurrentEvents}: HistoryNavBarProps) => {
  const { currentEntity, lastEntity, nextEntity } = readHistory()
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
        Back : {lastEntity ? lastEntity.entity.name : ''}
      </NavButton>
      <FocusHeader>{currentEntity.entity.name}</FocusHeader>
      <NavButton
        onClick={navigateForward}
      >
        Forward : {nextEntity ? nextEntity.entity.name : ''}
      </NavButton>
    </NavBar>
  )
}