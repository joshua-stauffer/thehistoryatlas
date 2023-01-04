import { useEffect, useRef } from "react";
import L, { Marker } from "leaflet";
import { MapContainer } from "./style";
import { MarkerData, FocusedGeoEntity } from "../../types";
import { getBoundingBox } from "../../pureFunctions/getBoundingBox";
import { mapTiles } from "./mapTiles";

interface MapProps {
  markers: MarkerData[];
  focusedGeoEntities: FocusedGeoEntity[];
}

export const MapView = (props: MapProps) => {
  const { markers, focusedGeoEntities } = props;

  const markerRef = useRef<Marker[]>([]);
  const mapRef = useRef<L.Map | undefined>();
  const markerLayerRef = useRef<L.LayerGroup | undefined>();

  // check for map's existence, and create it if need be
  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map("map", {
        layers: [mapTiles.natGeoWorld],
      });
    }
    markerLayerRef.current = L.layerGroup().addTo(mapRef.current);
  }, []);

  // ensure we're zoomed and centered on the current data page
  useEffect(() => {
    if (!mapRef.current) return;
    if (!markers.length) return;
    const boundingBox = getBoundingBox(markers);
    mapRef.current.fitBounds(boundingBox);
  }, [markers]);

  // add and update markers for places in current data page
  useEffect(() => {
    if (!mapRef.current) return;
    if (!markerLayerRef.current) return;
    markerLayerRef.current.clearLayers();
    markerRef.current = markers.map((markerData, i) => {
      if (!markerLayerRef.current) throw new Error("Missing markerLayeRef!");
      const { coords, text, guid } = markerData;
      const el = new L.Marker(coords).addTo(markerLayerRef.current);
      if (focusedGeoEntities.find((entity) => entity.GUID === guid)) {
        el.bindPopup(text).openPopup();
      } else {
        el.bindPopup(text);
      }
      return el;
    });
  }, [markers, focusedGeoEntities]);

  return <MapContainer id={"map"} />;
};
