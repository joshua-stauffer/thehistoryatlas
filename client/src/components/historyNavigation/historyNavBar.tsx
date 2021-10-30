import { readHistory, navigateHistoryBack, navigateHistoryForward } from "../../hooks/history"
import { NavBar, ActiveNavButton, NavButton, FocusHeader } from "./style"
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
      { lastEntity
        ?  <ActiveNavButton
              onClick={navigateBack}
            >
              Back {'( ' + lastEntity.entity.name + ' )'}
            </ActiveNavButton>
        :  <NavButton
              disabled
            >
              Back 
            </NavButton>
      }
      
      <FocusHeader>{Icon} {currentEntity.entity.name}</FocusHeader>
      
      { nextEntity
        ?  <ActiveNavButton
              onClick={navigateForward}
            >
              Forward {'( ' + nextEntity.entity.name + ' )'}
            </ActiveNavButton>
        :  <NavButton
              disabled
            >
              Forward 
            </NavButton>
      }
      
    </NavBar>
  )
}