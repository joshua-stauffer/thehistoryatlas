import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import EmblaCarousel from './carousel';
import { mockHistoryEvent } from '../../__mocks__/mockData';
import * as emblaCarousel from 'embla-carousel-react';

const mockScrollPrev = jest.fn();
const mockScrollNext = jest.fn();
const mockOn = jest.fn();
const mockOff = jest.fn();
const mockSlidesInView = jest.fn().mockReturnValue([0]);

// Mock the useEmblaCarousel hook
jest.mock('embla-carousel-react', () => ({
  useEmblaCarousel: jest.fn().mockImplementation(() => {
    const mockRef = { current: null };
    const mockApi = {
      scrollPrev: mockScrollPrev,
      scrollNext: mockScrollNext,
      on: mockOn,
      off: mockOff,
      slidesInView: mockSlidesInView,
    };
    return [mockRef, mockApi];
  }),
}));

describe('EmblaCarousel', () => {
  const mockSetFocusedIndex = jest.fn();
  const mockLoadNext = jest.fn().mockResolvedValue(undefined);
  const mockLoadPrev = jest.fn().mockResolvedValue(undefined);
  
  const mockSlides = [
    <div key="slide1" data-testid="slide-1">
      {mockHistoryEvent.text}
    </div>,
  ];
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders the carousel with navigation buttons', () => {
    render(
      <EmblaCarousel
        slides={mockSlides}
        setFocusedIndex={mockSetFocusedIndex}
        startIndex={0}
        loadNext={mockLoadNext}
        loadPrev={mockLoadPrev}
      />
    );
    
    // Check if navigation buttons are rendered
    expect(screen.getByText('Previous Event')).toBeInTheDocument();
    expect(screen.getByText('Next Event')).toBeInTheDocument();
    
    // Check if slides are rendered
    expect(screen.getByTestId('slide-1')).toBeInTheDocument();
  });
  
  test('clicking navigation buttons calls correct functions', async () => {
    render(
      <EmblaCarousel
        slides={mockSlides}
        setFocusedIndex={mockSetFocusedIndex}
        startIndex={0}
        loadNext={mockLoadNext}
        loadPrev={mockLoadPrev}
      />
    );
    
    // Get navigation buttons
    const prevButton = screen.getByText('Previous Event');
    const nextButton = screen.getByText('Next Event');
    
    // Click previous button
    fireEvent.click(prevButton);
    expect(mockScrollPrev).toHaveBeenCalled();
    
    // Click next button
    fireEvent.click(nextButton);
    expect(mockScrollNext).toHaveBeenCalled();
  });
  
  test('runs event handlers correctly', async () => {
    render(
      <EmblaCarousel
        slides={mockSlides}
        setFocusedIndex={mockSetFocusedIndex}
        startIndex={0}
        loadNext={mockLoadNext}
        loadPrev={mockLoadPrev}
      />
    );
    
    // Verify event handlers were set up
    expect(mockOn).toHaveBeenCalledWith('scroll', expect.any(Function));
    
    // Get the scroll handler
    const scrollHandler = mockOn.mock.calls[0][1];
    
    // Call the scroll handler
    await act(async () => {
      scrollHandler();
    });
    
    // Should call setFocusedIndex
    expect(mockSetFocusedIndex).toHaveBeenCalledWith(0);
  });
}); 