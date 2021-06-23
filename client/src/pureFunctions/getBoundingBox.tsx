import { MarkerData } from "../types";
import L from "leaflet"

export const getBoundingBox = (markers: MarkerData[]): L.LatLngBounds => {
  let maxLat: number = markers[0].coords[0];
  let maxLng: number = markers[0].coords[1];
  let minLat: number = markers[0].coords[0];
  let minLng: number = markers[0].coords[1];
  for (const { coords } of markers) {
    // check latitude
    if (coords[0] > maxLat) {
      maxLat = coords[0]
    } else if (coords[0] < minLat) {
      minLat = coords[0]
    }
    // check longitude
    if (coords[1] > maxLng) {
      maxLng = coords[1]
    } else if (coords[1] < minLng) {
      minLng = coords[1]
    }
  }
  const maxCorner = L.latLng(maxLat, maxLng)
  const minCorner = L.latLng(minLat, minLng)
  const boundingBox = new L.LatLngBounds(maxCorner, minCorner)
  return boundingBox
}