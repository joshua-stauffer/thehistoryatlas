import { makeVar } from '@apollo/client';
import { Entity, HistoryEntity } from '../types';

export const currentEntity = makeVar<HistoryEntity | null>(null)
export const historyBackVar = makeVar<HistoryEntity[]>([])
export const historyForwardVar = makeVar<HistoryEntity[]>([])

interface readHistoryResult {
  lastEntity: HistoryEntity | null;
  currentEntity: HistoryEntity | null;
  nextEntity: HistoryEntity | null;
}

export const readHistory = (): readHistoryResult => {
  const past = historyBackVar()
  const future = historyForwardVar()
  const current = currentEntity()
  return {
    lastEntity: past.length ? past[past.length - 1] : null,
    currentEntity: current,
    nextEntity: future.length ? future[future.length - 1] : null
  }
}

export interface addToHistoryProps {
  entity: Entity;
  lastSummaryGUID?: string;
}

export const addToHistory = (props: addToHistoryProps) => {
  const { entity, lastSummaryGUID } = props;
  const currentHistory = historyBackVar()
  let oldCurrentEntity = currentEntity()
  // if there isn't a currently selected entity, there's no need to push it to history
  if (oldCurrentEntity){
    oldCurrentEntity = {...oldCurrentEntity, rootEventID: lastSummaryGUID};
    historyBackVar([...currentHistory, oldCurrentEntity])
  }
  currentEntity({
    entity: entity,
    rootEventID: lastSummaryGUID
  })
  // now that we've navigated forwards, clear the future cache
  historyForwardVar([])
  console.log('current is now ', currentEntity())
}

export const navigateHistoryBack = () => {
  const oldCurrentEntity = currentEntity()
  if (!oldCurrentEntity) return;
  const currentHistory = historyBackVar()
  // can't navigate back if there is no history
  if (!currentHistory.length) return;
  const currentFuture = historyForwardVar()
  const newHistory = currentHistory.slice(0, -1)
  const newCurrentEntity = currentHistory.slice(-1)[0]
  currentEntity(newCurrentEntity)
  historyBackVar([...newHistory])
  historyForwardVar([...currentFuture, oldCurrentEntity])
}

export const navigateHistoryForward = () => {
  const oldCurrentEntity = currentEntity()
  if (!oldCurrentEntity) return;
  const currentFuture = historyForwardVar()
    // can't navigate forward if there is no history
  if (!currentFuture.length) return;
  const currentHistory = historyBackVar()
  const newFuture = currentFuture.slice(0, -1)
  const newCurrentEntity = currentFuture.slice(-1)[0]
  currentEntity(newCurrentEntity)
  historyBackVar([...currentHistory, oldCurrentEntity])
  historyForwardVar([...newFuture])
}

export const updateRootSummary = (guid: string): void => {
  const current = currentEntity();
  if (!current) return;
  currentEntity({
    ...current,
    rootEventID: guid
  })
}