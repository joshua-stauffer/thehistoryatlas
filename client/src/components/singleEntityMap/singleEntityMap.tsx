import { Skeleton } from "@mui/material";
import PersonIcon from "@mui/icons-material/Person";
import PlaceIcon from "@mui/icons-material/Place";
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet";
import { mapTiles } from "../map/mapTiles";
import L from "leaflet";
import React, { useCallback, useEffect, useRef } from "react";
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

const primaryEventIcon = L.divIcon({
  className: "primary-event-flag",
  html: '<div></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
  popupAnchor: [0, -10],
});

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
      <Marker key={`main-${i}`} position={[latitude, longitude]} icon={primaryEventIcon}>
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
        <NearbyEventMarker key={`${event.eventId}-${event.storyId}`} event={event} />
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

const NearbyEventMarker = ({ event }: { event: NearbyEvent }) => {
  const markerRef = useRef<L.Marker | null>(null);
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancelClose = useCallback(() => {
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  const scheduleClose = useCallback(() => {
    cancelClose();
    closeTimerRef.current = setTimeout(() => {
      markerRef.current?.closePopup();
    }, 200);
  }, [cancelClose]);

  return (
    <Marker
      ref={markerRef}
      position={[event.latitude, event.longitude]}
      icon={nearbyEventIcon}
      eventHandlers={{
        mouseover: () => { cancelClose(); markerRef.current?.openPopup(); },
        mouseout: scheduleClose,
      }}
    >
      <Popup>
        <div onMouseEnter={cancelClose} onMouseLeave={scheduleClose}>
          <NearbyEventPopup event={event} />
        </div>
      </Popup>
    </Marker>
  );
};

interface NearbyEventPopupProps {
  event: NearbyEvent;
}

const NearbyEventPopup = ({ event }: NearbyEventPopupProps) => (
  <div style={{ minWidth: 160, maxWidth: 260 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 2 }}>
      <PersonIcon style={{ fontSize: 14, color: "#555" }} />
      <span style={{ fontWeight: "bold", fontSize: "0.9em" }}>{event.personName}</span>
    </div>
    {event.personDescription && (
      <div style={{ fontSize: "0.82em", color: "#555", marginBottom: 6, marginLeft: 18 }}>
        {event.personDescription}
      </div>
    )}
    {event.summaryText && (
      <div style={{ fontSize: "0.82em", color: "#444", marginBottom: 6 }}>
        {event.summaryText}
      </div>
    )}
    <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 6 }}>
      <PlaceIcon style={{ fontSize: 14, color: "#555" }} />
      <span style={{ fontSize: "0.85em", color: "#555" }}>{event.placeName}</span>
    </div>
    <Link
      to={`/stories/${event.storyId}/events/${event.eventId}`}
      style={{ fontSize: "0.82em" }}
    >
      View story
    </Link>
  </div>
);
