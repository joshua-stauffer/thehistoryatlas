
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { mapTiles } from "../map/mapTiles"

type Size = "XS" | "SM" | "MD" | "LG" | "XL"

type tyleStyle = keyof(typeof mapTiles)

export interface SingleEntityMapProps {
  mapTyle: tyleStyle;
  latitude: number;
  longitude: number;
  zoom: number;
  size: Size;
  title: string;
}


export const SingleEntityMap = (props: SingleEntityMapProps) => {
  const { latitude, longitude, title, zoom } = props;
  return (
      <MapContainer center={[latitude, longitude]} zoom={zoom} scrollWheelZoom={false} style={{ height: "400px"}}>
        <TileLayer
          attribution='&copy; update'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}"
        />
        <MapInsides latitude={latitude} longitude={longitude} />
      <Marker position={[latitude, longitude]}>
        <Popup>
          {title}
        </Popup>
      </Marker>
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