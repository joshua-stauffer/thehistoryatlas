import { Skeleton } from '@mui/material'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { mapTiles } from "../map/mapTiles"

type Size = "XS" | "SM" | "MD" | "LG" | "XL"

type tyleStyle = keyof(typeof mapTiles)

export interface SingleEntityMapProps {
  mapTyle: tyleStyle;
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
  const { latitude, longitude, coords, title, zoom } = props;
  let lat: number, long: number;
  let markers;
  if (!latitude || !longitude) {
    if (!coords) {
      return (
        <Skeleton>

        </Skeleton>
      )
    }
    markers = coords.map(({latitude, longitude}) => (
      <Marker position={[latitude, longitude]}>
        <Popup>
          {title}
        </Popup>
      </Marker>
      )
    )
    // temporarily only considering the first place
    lat = coords[0].latitude
    long = coords[0].longitude
  } else {
    lat = latitude
    long = longitude
  }
    
  return (
      <MapContainer 
        center={[lat, long]} 
        zoom={zoom} 
        scrollWheelZoom={false} 
        style={{ 
          height: "300px", 
          width: "300px",
          margin: "10px"
        }}>
        <TileLayer
          attribution='&copy; update'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}"
        />
        <MapInsides latitude={lat} longitude={long} />
        {markers}
    </MapContainer>
  )
}

interface MapProps {
  latitude: number;
  longitude: number;
}

const MapInsides = (props: MapProps) => {
  // if new data is provided, update the map
  const { latitude, longitude } = props;
  const map = useMap()
  map.flyTo([latitude, longitude])
  return null
}