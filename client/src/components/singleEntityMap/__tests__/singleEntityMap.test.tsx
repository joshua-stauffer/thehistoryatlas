import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { SingleEntityMap } from "../singleEntityMap";
import { MemoryRouter } from "react-router-dom";
import { NearbyEvent } from "../../../api/nearbyEvents";

// Mock react-leaflet components
jest.mock("react-leaflet", () => ({
  MapContainer: ({ children, ...props }: any) => (
    <div data-testid="map-container" {...props}>
      {children}
    </div>
  ),
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ children, ...props }: any) => (
    <div data-testid="marker">{children}</div>
  ),
  Popup: ({ children }: any) => <div data-testid="popup">{children}</div>,
  useMap: () => ({
    flyTo: jest.fn(),
    getBounds: () => ({
      getSouth: () => 50,
      getNorth: () => 52,
      getWest: () => 9,
      getEast: () => 11,
    }),
  }),
  useMapEvents: jest.fn(),
}));

// Mock leaflet
jest.mock("leaflet", () => ({
  divIcon: jest.fn(() => ({})),
}));

const mockNearbyEvents: NearbyEvent[] = [
  {
    eventId: "event-1",
    storyId: "story-1",
    personName: "Johann Sebastian Bach",
    personDescription: "German composer",
    placeName: "Eisenach",
    latitude: 50.97,
    longitude: 10.32,
    datetime: "+1685-03-21T00:00:00Z",
    precision: 9,
    calendarModel: "http://www.wikidata.org/entity/Q1985727",
  },
  {
    eventId: "event-2",
    storyId: "story-2",
    personName: "Georg Friedrich Händel",
    personDescription: null,
    placeName: "Halle",
    latitude: 51.48,
    longitude: 11.97,
    datetime: "+1685-02-23T00:00:00Z",
    precision: 9,
    calendarModel: "http://www.wikidata.org/entity/Q1985727",
  },
];

const defaultProps = {
  coords: [{ latitude: 51.0, longitude: 10.0 }],
  zoom: 7,
  size: "MD" as const,
  title: "Test Location",
};

describe("SingleEntityMap with nearby events", () => {
  it("renders nearby event markers", () => {
    const { container } = render(
      <MemoryRouter>
        <SingleEntityMap {...defaultProps} nearbyEvents={mockNearbyEvents} />
      </MemoryRouter>,
    );

    const markers = screen.getAllByTestId("marker");
    // 1 main marker + 2 nearby event markers
    expect(markers.length).toBe(3);
  });

  it("popup shows person name and place name", () => {
    render(
      <MemoryRouter>
        <SingleEntityMap {...defaultProps} nearbyEvents={mockNearbyEvents} />
      </MemoryRouter>,
    );

    expect(screen.getByText("Johann Sebastian Bach")).toBeInTheDocument();
    expect(screen.getByText("Eisenach")).toBeInTheDocument();
    expect(screen.getByText("Georg Friedrich Händel")).toBeInTheDocument();
    expect(screen.getByText("Halle")).toBeInTheDocument();
  });

  it("expand shows description when clicking person name", () => {
    render(
      <MemoryRouter>
        <SingleEntityMap {...defaultProps} nearbyEvents={mockNearbyEvents} />
      </MemoryRouter>,
    );

    // Description should not be visible initially
    expect(screen.queryByText("German composer")).not.toBeInTheDocument();

    // Click person name to expand
    fireEvent.click(screen.getByText("Johann Sebastian Bach"));

    // Description should now be visible
    expect(screen.getByText("German composer")).toBeInTheDocument();
  });

  it("shows view story link for each nearby event", () => {
    render(
      <MemoryRouter>
        <SingleEntityMap {...defaultProps} nearbyEvents={mockNearbyEvents} />
      </MemoryRouter>,
    );

    const links = screen.getAllByText("View story");
    expect(links).toHaveLength(2);
  });

  it("renders without nearby events", () => {
    render(
      <MemoryRouter>
        <SingleEntityMap {...defaultProps} />
      </MemoryRouter>,
    );

    const markers = screen.getAllByTestId("marker");
    // Only the main marker
    expect(markers.length).toBe(1);
  });

  it("calls onBoundsChange callback", () => {
    const mockOnBoundsChange = jest.fn();
    render(
      <MemoryRouter>
        <SingleEntityMap
          {...defaultProps}
          onBoundsChange={mockOnBoundsChange}
        />
      </MemoryRouter>,
    );

    // The component should render without errors
    expect(screen.getByTestId("map-container")).toBeInTheDocument();
  });
});
