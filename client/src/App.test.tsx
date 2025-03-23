import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { historyEventLoader } from './pages/historyEvent/historyEventLoader';

// Mock the historyEventLoader
jest.mock('./pages/historyEvent/historyEventLoader', () => ({
  historyEventLoader: jest.fn()
}));

// Mock createBrowserRouter to avoid actual routing
jest.mock('react-router-dom', () => ({
  createBrowserRouter: jest.fn(() => ({
    routes: []
  })),
  RouterProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="router-provider">{children}</div>,
}));

describe('App', () => {
  test('renders without crashing', () => {
    render(<App />);
    // The App component creates a router and provider, but doesn't have much content itself
    expect(document.querySelector('div')).toBeInTheDocument();
  });
}); 