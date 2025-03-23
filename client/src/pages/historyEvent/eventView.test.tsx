import React from 'react';
import { render, screen } from '@testing-library/react';
import { EventView } from './eventView';
import { mockHistoryEvent } from '../../__mocks__/mockData';
import { MemoryRouter } from 'react-router-dom';
import * as timeModule from '../../components/renderDateTime/time';
import { HistoryEvent, Person } from '../../graphql/events';

// Mock the renderDateTime function
jest.mock('../../components/renderDateTime/time', () => ({
  renderDateTime: jest.fn().mockReturnValue('Mocked Date Display'),
}));

describe('EventView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders event information correctly', () => {
    render(
      <MemoryRouter>
        <EventView event={mockHistoryEvent} />
      </MemoryRouter>
    );
    
    // Check if date is rendered
    const dateElement = screen.getByText('Mocked Date Display');
    expect(dateElement).toBeInTheDocument();
    
    // Check if source information is displayed
    expect(screen.getByText(/source:/i)).toBeInTheDocument();
    expect(
      screen.getByText(mockHistoryEvent.source.title)
    ).toBeInTheDocument();
    
    // Check if author information is displayed
    expect(screen.getByText(/authors:/i)).toBeInTheDocument();
    expect(
      screen.getByText(mockHistoryEvent.source.author, { exact: false })
    ).toBeInTheDocument();
    
    // Check if accessed date is displayed
    expect(screen.getByText(/accessed on:/i)).toBeInTheDocument();
    
    // Check if story links are rendered
    mockHistoryEvent.stories.forEach((story: { name: string }) => {
      expect(screen.getByText(story.name)).toBeInTheDocument();
    });
    
    // Check if text content is rendered
    expect(screen.getByText(mockHistoryEvent.text, { exact: false })).toBeInTheDocument();
  });

  test('renders tags correctly', () => {
    render(
      <MemoryRouter>
        <EventView event={mockHistoryEvent} />
      </MemoryRouter>
    );
    
    // Check if all tags are rendered as buttons
    mockHistoryEvent.tags.forEach(tag => {
      const tagElement = screen.getByText(tag.name);
      expect(tagElement).toBeInTheDocument();
      
      // Check if the tag is wrapped in a link with the correct URL
      const linkElement = tagElement.closest('a');
      expect(linkElement).toHaveAttribute(
        'href', 
        `/stories/${tag.defaultStoryId}/events/${mockHistoryEvent.id}`
      );
    });
  });

  test('renders non-tag text correctly', () => {
    // Simple event with just one tag to make testing easier
    const personTag: Person = {
      id: 'test-tag',
      type: 'PERSON',
      name: 'Person tag',
      startChar: 15,
      stopChar: 25,
      defaultStoryId: 'test-story',
    };
    
    const simpleEvent: HistoryEvent = {
      ...mockHistoryEvent,
      text: 'Test text with a Person tag.',
      tags: [personTag]
    };
    
    render(
      <MemoryRouter>
        <EventView event={simpleEvent} />
      </MemoryRouter>
    );
    
    // Check if text content is rendered correctly
    expect(screen.getByText(/Test text with a/i, { exact: false })).toBeInTheDocument();
    expect(screen.getByText('Person tag')).toBeInTheDocument();
    expect(screen.getByText(/\./i, { exact: false })).toBeInTheDocument();
  });
}); 