import { readHistory, navigateHistoryBack, navigateHistoryForward } from "../../history"
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
        Back : {lastEntity ? lastEntity.entity.type : ''}
      </NavButton>
      <FocusHeader>{currentEntity.entity.guid.slice(0, 6)} : {currentEntity.entity.type}</FocusHeader>
      <NavButton
        onClick={navigateForward}
      >
        Forward : {nextEntity ? nextEntity.entity.type : ''}
      </NavButton>
    </NavBar>
  )
}