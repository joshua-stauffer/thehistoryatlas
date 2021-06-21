import { readHistory, navigateHistoryBack, navigateHistoryForward } from "../../history"
import { NavBar, NavButton, FocusHeader } from "./style"

export const HistoryNavBar = () => {
  const { currentEntity, lastEntity, nextEntity } = readHistory()
  return (
    <NavBar>
      <NavButton
        onClick={navigateHistoryBack}
      >
        Back : {lastEntity ? lastEntity.entity.type : ''}
      </NavButton>
      <FocusHeader>{currentEntity.entity.guid.slice(0, 6)} : {currentEntity.entity.type}</FocusHeader>
      <NavButton
        onClick={navigateHistoryForward}
      >
        Forward : {nextEntity ? nextEntity.entity.type : ''}
      </NavButton>
    </NavBar>
  )
}