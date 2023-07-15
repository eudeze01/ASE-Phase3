import * as db from "./dbstub.js";
import mapstyles from "./mapstyle.js";

// Import Google Maps
const GOOGLE_API_KEY = "";

((g) => {
  var h,
    a,
    k,
    p = "The Google Maps JavaScript API",
    c = "google",
    l = "importLibrary",
    q = "__ib__",
    m = document,
    b = window;
  b = b[c] || (b[c] = {});
  var d = b.maps || (b.maps = {}),
    r = new Set(),
    e = new URLSearchParams(),
    u = () =>
      h ||
      (h = new Promise(async (f, n) => {
        await (a = m.createElement("script"));
        e.set("libraries", [...r] + "");
        for (k in g)
          e.set(
            k.replace(/[A-Z]/g, (t) => "_" + t[0].toLowerCase()),
            g[k]
          );
        e.set("callback", c + ".maps." + q);
        a.src = `https://maps.${c}apis.com/maps/api/js?` + e;
        d[q] = f;
        a.onerror = () => (h = n(Error(p + " could not load.")));
        a.nonce = m.querySelector("script[nonce]")?.nonce || "";
        m.head.append(a);
      }));
  d[l]
    ? console.warn(p + " only loads once. Ignoring:", g)
    : (d[l] = (f, ...n) => r.add(f) && u().then(() => d[l](f, ...n)));
})({ key: GOOGLE_API_KEY, v: "beta" });

const { Map } = await google.maps.importLibrary("maps");
const { Marker } = await google.maps.importLibrary("marker");

// Initialize variables
let map;
let vehicleMarkers = [];
const centerPos = { lat: 51.5195786, lng: -0.0606907 };
const carIcon = {
  url: "/images/car.png",
  scaledSize: new google.maps.Size(20, 43),
  origin: new google.maps.Point(0, 0),
  anchor: new google.maps.Point(0, 0),
};

// Initialize Map
async function initMap() {
  map = new Map(document.getElementById("GMap"), {
    zoom: 13,
    center: centerPos,
    mapId: "",
  });

  map.setOptions({ styles: mapstyles.darkStyle });
}

initMap().then(() => {
  // retrieveVehicles();
});

// Remove vehicle markers from map
function removeVehicleMarkers() {
  vehicleMarkers.forEach((e) => {
    e.setMap(null);
  });
  vehicleMarkers = [];
}

// Retrive vehicle positions from API and
// display them on the map
function _showAllVehicles() {
  removeVehicleMarkers();
  vehicleMarkers = [];

  db.getVehicles().then((c) => {
    if (Array.isArray(c)) {
      c.forEach((v_pos) => {
        if (
          (v_pos.id !== "undefined") &
          (v_pos.lat !== "undefined") &
          (v_pos.lng !== "undefined")
        ) {
          try {
            let pos = {
              lat: parseFloat(v_pos.lat),
              lng: parseFloat(v_pos.lng),
            };

            const marker = new Marker({
              position: pos,
              map,
              icon: carIcon,
            });
            console.log(v_pos);
            // For debugging purpose
            new google.maps.InfoWindow({
              content: v_pos.id + "-" + v_pos.type,
            }).open({
              anchor: marker,
              map,
            });
            // End For debugging purpose

            vehicleMarkers.push(marker);
          } catch (error) {
            console.error(error);
          }
        }
      });
    }
  });
}

function _addVehicle(lat, lng, content) {
  const marker = new Marker({
    position: { lat: lat, lng: lng },
    map,
    icon: carIcon,
  });
  // For debugging purpose
  new google.maps.InfoWindow({
    content: content,
  }).open({
    anchor: marker,
    map,
  });
  // End For debugging purpose

  vehicleMarkers.push(marker);
}

function _drawLine(latLngArray) {
  // console.log(latLngArray);
  const path = new google.maps.Polyline({
    path: latLngArray,
    strokeColor: "#0043FD",
    strokeOpacity: 1.0,
    strokeWeight: 5,
  });

  path.setMap(map);

  return path;
}

export const mapObject = map;
export const drawPolyLine = _drawLine;
export const showAllVehicles = _showAllVehicles;
export const removeMapVehicles = removeVehicleMarkers;
export const addVehicle = _addVehicle;
