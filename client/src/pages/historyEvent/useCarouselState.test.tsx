import { renderHook, act } from '@testing-library/react-hooks';
import { useCarouselState } from './useCarouselState';
import { mockHistoryEvent, mockHistoryEvent2 } from '../../__mocks__/mockData';
import { HistoryEvent } from '../../graphql/events';
import React from 'react';

describe('useCarouselState', () => {
  const mockLoadFn = jest.fn();
  const initialEvents = [mockHistoryEvent, mockHistoryEvent2];
  const initialIndex = 0;
  
  beforeEach(() => {
    mockLoadFn.mockClear();
  });
  
  test('initializes with given events and index', () => {
    const { result } = renderHook(() => 
      useCarouselState(initialEvents, initialIndex)
    );
    
    expect(result.current.historyEvents).toEqual(initialEvents);
    expect(result.current.currentEventIndex).toBe(initialIndex);
  });
  
  test('updates currentEventIndex when setCurrentEventIndex is called', () => {
    const { result } = renderHook(() => 
      useCarouselState(initialEvents, initialIndex)
    );
    
    act(() => {
      result.current.setCurrentEventIndex(1);
    });
    
    expect(result.current.currentEventIndex).toBe(1);
  });
  
  test('loads more events to the right', async () => {
    const newEvents = [
      {
        ...mockHistoryEvent,
        id: 'new-event-1',
      },
      {
        ...mockHistoryEvent2,
        id: 'new-event-2',
      }
    ];
    
    mockLoadFn.mockResolvedValueOnce(newEvents);
    const { result } = renderHook(() => 
      useCarouselState(initialEvents, initialIndex)
    );
    
    await act(async () => {
      await result.current.loadMoreEvents('right', mockLoadFn);
    });
    
    expect(result.current.historyEvents).toEqual([...initialEvents, ...newEvents]);
    expect(result.current.currentEventIndex).toBe(initialIndex);
  });
  
  test('loads more events to the left', async () => {
    const newEvents = [
      {
        ...mockHistoryEvent,
        id: 'new-event-3',
      },
      {
        ...mockHistoryEvent2,
        id: 'new-event-4',
      }
    ];
    
    mockLoadFn.mockResolvedValueOnce(newEvents);
    const { result } = renderHook(() => 
      useCarouselState(initialEvents, initialIndex)
    );
    
    await act(async () => {
      await result.current.loadMoreEvents('left', mockLoadFn);
    });
    
    expect(result.current.historyEvents).toEqual([...newEvents, ...initialEvents]);
    expect(result.current.currentEventIndex).toBe(newEvents.length);
  });
  
  test('updates when initialEvents and initialIndex change', () => {
    const newInitialEvents = [mockHistoryEvent2];
    const newInitialIndex = 0;
    
    interface HookProps {
      events: HistoryEvent[];
      index: number;
    }
    
    const { result, rerender } = renderHook(
      ({ events, index }: HookProps) => useCarouselState(events, index),
      { 
        initialProps: { 
          events: initialEvents, 
          index: initialIndex 
        } 
      }
    );
    
    expect(result.current.historyEvents).toEqual(initialEvents);
    expect(result.current.currentEventIndex).toBe(initialIndex);
    
    rerender({ 
      events: newInitialEvents, 
      index: newInitialIndex 
    });
    
    expect(result.current.historyEvents).toEqual(newInitialEvents);
    expect(result.current.currentEventIndex).toBe(newInitialIndex);
  });
}); 