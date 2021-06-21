import { makeVar } from '@apollo/client';
import { HistoryEntity } from './types';

export const currentEntity = makeVar<HistoryEntity>({
  // a default start value, can be removed once we're starting on search page
  entity: {
    guid: 'bd025284-890b-42c5-88a7-27f417737955',
    type: 'PERSON'
  }
})
export const historyBackVar = makeVar<HistoryEntity[]>([])
export const historyForwardVar = makeVar<HistoryEntity[]>([])

interface readHistoryResult {
  lastEntity: HistoryEntity | null;
  currentEntity: HistoryEntity;
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

export const addToHistory = (entity: HistoryEntity ) => {
  const currentHistory = historyBackVar()
  const oldCurrentEntity = currentEntity()
  currentEntity(entity)
  historyBackVar([...currentHistory, oldCurrentEntity])
  // now that we've navigated forwards, clear the future cache
  historyForwardVar([])
}

export const navigateHistoryBack = () => {
  const currentHistory = historyBackVar()
  // can't navigate back if there is no history
  if (!currentHistory.length) return;
  const currentFuture = historyForwardVar()
  const newHistory = currentHistory.slice(0, -1)
  const newCurrentEntity = currentHistory.slice(-1)[0]
  const oldCurrentEntity = currentEntity()
  currentEntity(newCurrentEntity)
  historyBackVar([...newHistory])
  historyForwardVar([...currentFuture, oldCurrentEntity])
}

export const navigateHistoryForward = () => {
  const currentFuture = historyForwardVar()
    // can't navigate forward if there is no history
  if (!currentFuture.length) return;
  const currentHistory = historyBackVar()
  const newFuture = currentFuture.slice(0, -1)
  const newCurrentEntity = currentFuture.slice(-1)[0]
  const oldCurrentEntity = currentEntity()
  currentEntity(newCurrentEntity)
  historyBackVar([...currentHistory, oldCurrentEntity])
  historyForwardVar([...newFuture])
}
