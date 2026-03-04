import { Skeleton } from "@mui/material";
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet";
import { mapTiles } from "../map/mapTiles";
import L from "leaflet";
import React, { useState, useCallback, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { NearbyEvent } from "../../api/nearbyEvents";

type Size = "SM" | "MD" | "LG";

const mapDimensions = {
  SM: {
    height: "300px",
    width: "300px",
    margin: "10px",
  },
  MD: {
    height: "100%",
    width: "100%",
    margin: "0",
  },
  LG: {
    height: "90vh",
    width: "100%",
    margin: "30px",
  },
};

export interface MapBounds {
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
}

export interface SingleEntityMapProps {
  latitude?: number;
  longitude?: number;
  coords?: {
    latitude: number;
    longitude: number;
  }[];
  zoom: number;
  size: Size;
  title: string;
  nearbyEvents?: NearbyEvent[];
  onBoundsChange?: (bounds: MapBounds) => void;
}

const nearbyEventIcon = L.divIcon({
  className: "nearby-event-flag",
  html: '<div></div>',
  iconSize: [10, 10],
  iconAnchor: [5, 5],
  popupAnchor: [0, -8],
});

export const SingleEntityMap = (props: SingleEntityMapProps) => {
  const { size, latitude, longitude, coords, title, zoom, nearbyEvents, onBoundsChange } = props;
  let lat: number, long: number;
  let markers;
  if (!latitude || !longitude) {
    if (!coords) {
      return <Skeleton></Skeleton>;
    }
    markers = coords.map(({ latitude, longitude }, i) => (
      <Marker key={`main-${i}`} position={[latitude, longitude]}>
        <Popup>{title}</Popup>
      </Marker>
    ));
    // only considering the first place
    lat = coords.length ? coords[0].latitude : 0;
    long = coords.length ? coords[0].longitude : 0;
  } else {
    lat = latitude;
    long = longitude;
  }

  return (
    <MapContainer
      center={[lat, long]}
      zoom={zoom}
      scrollWheelZoom={false}
      style={{
        height: mapDimensions[size].height,
        width: mapDimensions[size].width,
        margin: mapDimensions[size].margin,
        padding: 0,
      }}
    >
      <TileLayer
        attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community"
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
      />
      <MapInsides latitude={lat} longitude={long} onBoundsChange={onBoundsChange} />
      {markers}
      {nearbyEvents?.map((event) => (
        <Marker
          key={`${event.eventId}-${event.storyId}`}
          position={[event.latitude, event.longitude]}
          icon={nearbyEventIcon}
        >
          <Popup>
            <NearbyEventPopup event={event} />
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

interface MapProps {
  latitude: number;
  longitude: number;
  onBoundsChange?: (bounds: MapBounds) => void;
}

const MapInsides = (props: MapProps) => {
  // if new data is provided, update the map
  const { latitude, longitude, onBoundsChange } = props;
  const map = useMap();
  const prevCoords = useRef<{ latitude: number; longitude: number } | null>(null);

  useEffect(() => {
    if (
      prevCoords.current?.latitude !== latitude ||
      prevCoords.current?.longitude !== longitude
    ) {
      prevCoords.current = { latitude, longitude };
      map.flyTo([latitude, longitude], undefined, {
        animate: false,
        duration: 0.5,
      });
    }
  }, [map, latitude, longitude]);

  const reportBounds = useCallback(() => {
    if (!onBoundsChange) return;
    const bounds = map.getBounds();
    onBoundsChange({
      minLat: bounds.getSouth(),
      maxLat: bounds.getNorth(),
      minLng: bounds.getWest(),
      maxLng: bounds.getEast(),
    });
  }, [map, onBoundsChange]);

  useMapEvents({
    moveend: reportBounds,
    load: reportBounds,
  });

  // Report initial bounds
  useEffect(() => {
    reportBounds();
  }, [reportBounds]);

  return null;
};

interface NearbyEventPopupProps {
  event: NearbyEvent;
}

const NearbyEventPopup = ({ event }: NearbyEventPopupProps) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{ minWidth: 150, maxWidth: 250 }}>
      <div
        style={{ cursor: "pointer", fontWeight: "bold", marginBottom: 4 }}
        onClick={() => setExpanded(!expanded)}
      >
        {event.personName}
      </div>
      {expanded && event.personDescription && (
        <div style={{ fontSize: "0.85em", color: "#555", marginBottom: 4 }}>
          {event.personDescription}
        </div>
      )}
      <div style={{ fontSize: "0.85em", color: "#666" }}>{event.placeName}</div>
      <div style={{ marginTop: 6 }}>
        <Link
          to={`/stories/${event.storyId}/events/${event.eventId}`}
          style={{ fontSize: "0.85em" }}
        >
          View story
        </Link>
      </div>
    </div>
  );
};
