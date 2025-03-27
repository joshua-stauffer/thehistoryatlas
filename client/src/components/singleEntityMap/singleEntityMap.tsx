import { Skeleton } from "@mui/material";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import { mapTiles } from "../map/mapTiles";

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
}

export const SingleEntityMap = (props: SingleEntityMapProps) => {
  const { size, latitude, longitude, coords, title, zoom } = props;
  let lat: number, long: number;
  let markers;
  if (!latitude || !longitude) {
    if (!coords) {
      return <Skeleton></Skeleton>;
    }
    markers = coords.map(({ latitude, longitude }) => (
      <Marker position={[latitude, longitude]}>
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
      <MapInsides latitude={lat} longitude={long} />
      {markers}
    </MapContainer>
  );
};

interface MapProps {
  latitude: number;
  longitude: number;
}

const MapInsides = (props: MapProps) => {
  // if new data is provided, update the map
  const { latitude, longitude } = props;
  const map = useMap();
  map.flyTo([latitude, longitude], undefined, {
    animate: false,
    duration: 0.5,
  });
  return null;
};
