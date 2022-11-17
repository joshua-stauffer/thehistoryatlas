import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { useState } from 'react'
import styled from 'styled-components'

interface SimpleMapProps {
  latitude: number;
  longitude: number;
}

const Div = styled.div`
  height: 300px;
  width: 300px;
`


export const SimpleMap = (props: SimpleMapProps) => {
  const { latitude, longitude } = props;
  const [mapId] = useState("map")
  return (
    <Div id={mapId}>
      <MapContainer center={[latitude, longitude]} scrollWheelZoom={false} zoom={13}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[latitude, longitude]}>
          <Popup>Something is here!</Popup>
        </Marker>
      </MapContainer>
    </Div>
  )
}
