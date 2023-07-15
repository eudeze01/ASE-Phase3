// const vehicles = [
//   { id: "mXfkjrFw", lat: 51.5090562, lng: -0.1304571 },
//   { id: "nZXB8ZHz", lat: 51.5080898, lng: -0.07620836346036469 },
//   { id: "Tkwu74WC", lat: 51.5425649, lng: -0.00693080308689057 },
//   { id: "5KWpnAJN", lat: 51.519821199999996, lng: -0.09397523701275332 },
//   { id: "uf5ZrXYw", lat: 51.5133798, lng: -0.0889552 },
//   { id: "VMerzMH8", lat: 51.5253378, lng: -0.033435 },
//   { id: "8efT67Xd", lat: 51.54458615, lng: -0.0161905117168855 },
// ];

export async function getVehicles() {
  return await (await fetch("/api/getCurrentVehicles")).json();
}

export async function getBingKey() {
  const obj = await (await fetch("/api/getBingKey")).json();
  return obj.key;
}
