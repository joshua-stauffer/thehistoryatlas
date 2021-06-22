import { useEffect, useRef } from 'react';
import L, { Marker } from 'leaflet';
import { MapContainer } from './style';
import { MarkerData, FocusedGeoEntity } from '../../types';

interface MapProps {
  latitude: number;
  longitude: number;
  zoom: number;
  markers: MarkerData[];
  focusedGeoEntities: FocusedGeoEntity[];
}



export const Map = (props: MapProps) => {
  const { latitude, longitude, markers, zoom, focusedGeoEntities } = props;

  const markerRef = useRef<Marker[]>([])
  const mapRef = useRef<L.Map | undefined>()
  const markerLayerRef = useRef<L.LayerGroup | undefined>()
  useEffect(() => console.log(`markerRef: ${markerRef.current}`))

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map('map', {
        center: [latitude, longitude],
        zoom: zoom,
        layers: [
          L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            attribution:
              '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
          }),
        ]
      })
    } else {
      const { coords } = focusedGeoEntities[0];
      const latLong = new L.LatLng(coords.latitude, coords.longitude);
      mapRef.current.flyTo(latLong, zoom, {
        duration: 2
      })
    }
    markerLayerRef.current = L.layerGroup().addTo(mapRef.current)
  }, [latitude, longitude, zoom, focusedGeoEntities])

  useEffect(() => {
    if (!mapRef.current) return;
    if (!markerLayerRef.current) return;
    console.log('updating markerRef: ', markerRef.current)
    markerLayerRef.current.clearLayers()
    markerRef.current = markers.map((markerData, i) => {
      if (!markerLayerRef.current) throw new Error('What!')
      const { coords, text, guid } = markerData;
      const el = new L.Marker(coords).addTo(markerLayerRef.current)
      if (focusedGeoEntities.find(entity => entity.GUID === guid)){
        el.bindPopup(text).openPopup()
      } else {
        el.bindPopup(text)
      }
      return el;
    })
  }, [markers, focusedGeoEntities])

  return (
    <MapContainer id={"map"}/>
  )
}