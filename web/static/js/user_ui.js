console.log("UI");

let mapObj, MapsInterface;
let choosingStart = false,
  choosingDest = false;
let startMarker, destMarker;
let journeyPathLine;
let journeyStarted = false,
  journeyEnded = false;

let start_rating = 0;

// Elements
const input_start = document.getElementById("input_start");
const input_destination = document.getElementById("input_destination");
const btn_book_vehicle = document.getElementById("book_vehicle");
const btn_select_map_start = document.getElementById("btn_select_map_start");
const btn_select_map_destination = document.getElementById(
  "btn_select_map_destination"
);
const start_jny = document.getElementById("start_journey");
const booking_title = document.getElementById("booking_title");
const ui_controls = document.getElementById("ui_controls");
const rating_view = document.getElementById("rating_view");
const confirm_info_view = document.getElementById("confirm_info");
const route_details = document.getElementById("route_details");

export const InitializeUI = function init_UI(map, mapInterface) {
  //   console.log(map);
  MapsInterface = mapInterface;
  mapObj = map;
  registerListeners();
  document.getElementById("input_start").disabled = true;
  document.getElementById("input_destination").disabled = true;

  // Check if booking is already available for this user
  fetch("/api/currentBooking").then((v) => {
    v.json().then((v) => {
      if (v.start_x && v.start_y && v.end_x && v.end_y) {
        enableSelectPositionControls(false);
        startMarker = new google.maps.Marker({
          position: { lat: Number(v.start_x), lng: Number(v.start_y) },
          map: mapObj,
        });

        destMarker = new google.maps.Marker({
          position: { lat: Number(v.end_x), lng: Number(v.end_y) },
          map: mapObj,
        });

        console.log(v);
        journeyStarted = v.started;
        journeyEnded = v.ended;
        updateUI();

        completeRouteSelection(startMarker, destMarker).then((v) => {
          journeyPathLine = v.polyLine;
        });
        viewBookedVehicleData(
          v.plate,
          v.model,
          v.type,
          v.driver_name,
          v.avg_rating
        );

        MapsInterface.addVehicle(Number(v.lat), Number(v.lng), "Your Vehicle");

        document.getElementById("time_to_arrive").innerText = "-";
        document.getElementById("confirm_info").classList.remove("d-none");
      } else {
        MapsInterface.showAllVehicles();
      }
    });
  });
};

function setStartInputUI(latLng) {
  if (startMarker) {
    document.getElementById("input_start").value =
      latLng.lat() + ", " + latLng.lng();
  }
}

function setDestInputUI(latLng) {
  if (destMarker) {
    document.getElementById("input_destination").value =
      latLng.lat() + ", " + latLng.lng();
  }
}

function showErrorToUser(message, title) {
  if (document.readyState == "complete") {
    document.querySelector("#errorModal .modal-title").innerHTML = title;
    document.querySelector("#errorModal .modal-body").innerHTML = message;

    const err_modal = new bootstrap.Modal(
      document.getElementById("errorModal")
    );

    err_modal.show();
  }
}

function vehicleBooked(data) {
  if (data.car_id) {
    document.getElementById("vehicle_id").innerText = data.car_id;
    document.getElementById("time_to_arrive").innerText =
      Number(data.total_time.toFixed(2)) + " mins";
    document.getElementById("confirm_info").classList.remove("d-none");
    booking_title.innerHTML =
      'Booking Confirmed <i class="bi bi-check-circle-fill ms-2 text-success"></i>';

    fetch(
      "/api/getVehicleDetails?" + new URLSearchParams({ id: data.car_id })
    ).then((res) => {
      // console.log(v.);
      res.json().then((v) => {
        console.log(v);
        viewBookedVehicleData(
          v.plate,
          v.model,
          v.type,
          v.driver_name,
          v.avg_rating
        );

        MapsInterface.addVehicle(Number(v.lat), Number(v.lng), "Your Vehicle");
      });
    });

    // console.log(MapsInterface);
    MapsInterface.removeMapVehicles();
  } else {
    // TODO : Present with message for no cars available.
  }
}

function viewBookedVehicleData(v_plate, model, type, driver_name, rating) {
  document.getElementById("vehicle_id").innerText = v_plate;
  document.getElementById("model").innerText = model;
  document.getElementById("type").innerText = type;
  document.getElementById("driver").innerText = driver_name;

  const star = document.createElement("i");
  star.classList.add("bi", "bi-star", "mx-2");
  const num = document.createElement("span");
  num.innerText = rating.toFixed(2) * 5 + "/5";
  num.classList.add("float-end");

  // document.getElementById(
  //   "rating"
  // ).innerHTML = `<i class="bi bi-star-fill"></i>${rating.toFixed(2)}`;
  const el = document.getElementById("rating");
  el.innerHTML = "";
  el.appendChild(star);
  el.appendChild(num);
}

function enableSelectPositionControls(enable = true) {
  // input_start.disabled = !enable;
  btn_select_map_start.disabled = !enable;
  choosingStart = choosingStart && enable;

  // input_destination.disabled = !enable;
  btn_select_map_destination.disabled = !enable;
  choosingDest = choosingDest && enable;

  btn_book_vehicle.disabled = !enable;

  if (!enable) {
    document.getElementById("btn_select_map_start").innerHTML =
      '<i class="bi bi-pin-map-fill"></i>';
    document.getElementById("btn_select_map_destination").innerHTML =
      '<i class="bi bi-pin-map-fill"></i>';
  }

  if (enable) {
    document
      .querySelectorAll("input[name=type]")
      .forEach((i) => i.removeAttribute("disabled"));
  } else {
    document
      .querySelectorAll("input[name=type]")
      .forEach((i) => i.setAttribute("disabled", true));
  }
}

async function completeRouteSelection(startMarker, endMarker) {
  if (document.BingKey) {
    // Get Route Data from Bing API
    const url = `http://dev.virtualearth.net/REST/V1/Routes/Driving?`;

    const parameters = {
      key: document.BingKey,
      avoid: "minimizeTolls",
      ra: "excludeItinerary,routePath",
      "wp.0":
        startMarker.getPosition().lat() +
        ", " +
        startMarker.getPosition().lng(),
      "wp.1":
        endMarker.getPosition().lat() + ", " + endMarker.getPosition().lng(),
    };

    const res = await fetch(url + new URLSearchParams(parameters));

    if (res.ok) {
      const data = await res.json();

      // Get Route as geo points
      const pos_array =
        data["resourceSets"][0]["resources"][0]["routePath"]["line"][
          "coordinates"
        ];

      const google_latlng_array = pos_array.map((v) => {
        return { lat: v[0], lng: v[1] };
      });

      // Calculate and View Fair
      let dist = data["resourceSets"][0]["resources"][0]["travelDistance"];
      dist = Number(dist);

      let fair = dist > 5 ? 6 + (dist - 5) : dist * 1.2;

      document.getElementById("distance").innerText = dist.toFixed(2) + " Km";
      document.getElementById("fair").innerHTML = fair.toFixed(2) + " &#163";
      route_details.classList.remove("d-none");

      return {
        polyLine: MapsInterface.drawPolyLine(google_latlng_array),
        distance: dist,
      };
    } else {
      return {
        error: res.statusText,
      };
    }
  }
}

function updateUI() {
  if (journeyStarted & !journeyEnded) {
    start_jny.innerText = "End Journey";
    booking_title.innerHTML =
      'Journey Started <i class="bi bi-car-front ms-2 text-success"></i>';
    ui_controls.classList.add("d-none");
  }

  if (journeyEnded) {
    confirm_info_view.classList.add("d-none");
    rating_view.classList.remove("d-none");
  }
}

function resetUIState() {
  rating_view.classList.add("d-none");
  enableSelectPositionControls();
  input_start.value = "";
  input_destination.value = "";
  choosingStart = false;
  choosingDest = false;
  journeyStarted = false;
  journeyEnded = false;
  start_jny.innerText = "Start Journey";
  route_details.classList.add("d-none");
  ui_controls.classList.remove("d-none");

  // Removing Start Marker
  if (startMarker) {
    startMarker.setMap(null);
    startMarker = null;
  }
  // Removing Destination Marker
  if (destMarker) {
    destMarker.setMap(null);
    destMarker = null;
  }
  // Remofing journey path line
  if (journeyPathLine && !journeyPathLine.error) {
    journeyPathLine.setMap(null);
    journeyPathLine = null;
  }

  MapsInterface.removeMapVehicles();
  MapsInterface.showAllVehicles();
}

function viewPrevJourneys() {
  if (document.readyState == "complete") {
    const t_body = document.getElementById("pj_t_body");
    fetch("/api/previousJourneys").then((res) => {
      if (res.ok) {
        res.json().then((prev_j) => {
          if (Array.isArray(prev_j)) {
            t_body.innerHTML = "";
            prev_j.forEach((rec) => {
              const t_row = document.createElement("tr");
              const id = document.createElement("td");
              id.innerText = rec.id;
              const type = document.createElement("td");
              type.innerText = rec.type;
              const plate = document.createElement("td");
              plate.innerText = rec.plate;
              const driver = document.createElement("td");
              driver.innerText = rec.driver_name;
              const start = document.createElement("td");
              start.innerText = rec.start_time;
              const end = document.createElement("td");
              end.innerText = rec.end_time;
              const rating = document.createElement("td");
              rating.innerText = rec.rating;
              // t_row.innerHTML
              t_row.appendChild(id);
              t_row.appendChild(type);
              t_row.appendChild(plate);
              t_row.appendChild(driver);
              t_row.appendChild(start);
              t_row.appendChild(end);
              t_row.appendChild(rating);
              t_body.append(t_row);
            });

            const modal = new bootstrap.Modal(
              document.getElementById("prev_journey")
            );
            modal.show();
          }
        });
      }
    });
  }
}

function registerListeners() {
  // Listner for selecting start and destination on the map
  mapObj.addListener("click", (e) => {
    if (choosingStart) {
      if (startMarker) {
        startMarker.setMap(null);
        startMarker = null;
      }

      startMarker = new google.maps.Marker({
        position: e.latLng,
        map: mapObj,
      });
      mapObj.panTo(e.latLng);

      const infowindow = new google.maps.InfoWindow({
        content: "Start Location",
        ariaLabel: "Start",
      });

      infowindow.open({
        anchor: startMarker,
        mapObj,
      });

      setStartInputUI(e.latLng);
    } else if (choosingDest) {
      if (destMarker) {
        destMarker.setMap(null);
        destMarker = null;
      }

      destMarker = new google.maps.Marker({
        position: e.latLng,
        map: mapObj,
      });
      mapObj.panTo(e.latLng);

      new google.maps.InfoWindow({
        content: "End Location",
        ariaLabel: "Start",
      }).open({
        anchor: destMarker,
        mapObj,
      });
      setDestInputUI(e.latLng);
    }

    if (startMarker && destMarker && (choosingStart || choosingDest)) {
      if (journeyPathLine && !journeyPathLine.error) {
        journeyPathLine.setMap(null);
        journeyPathLine = null;
      }

      completeRouteSelection(startMarker, destMarker)
        .then((v) => {
          // console.log(v);
          journeyPathLine = v.polyLine;
        })
        .catch((r) => {
          console.error(r);
        });
    }
  });

  btn_book_vehicle.addEventListener("click", async () => {
    if (startMarker && destMarker) {
      enableSelectPositionControls(false);

      //   Convert Path to string to send to server
      const path_arr = journeyPathLine.getPath()["g"];
      //   console.log();

      let parameters = {
        source: {
          x: startMarker.getPosition().lat(),
          y: startMarker.getPosition().lng(),
        },
        destination: {
          x: destMarker.getPosition().lat(),
          y: destMarker.getPosition().lng(),
        },
        pathArray: Array.from(path_arr).join(","),
        type: document.querySelector('input[name="type"]:checked').value,
      };

      const options = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(parameters),
      };

      fetch("/api/book", options).then(async (res) => {
        if (res.ok) {
          res.json().then((data) => {
            if (!data.car_id) {
              showErrorToUser(
                "Sorry! No vehicles for the selected type are available at the moment",
                "Error"
              );
              return;
            }
            vehicleBooked(data);
          });
        } else {
          //View an error of booking failed.
          showErrorToUser(
            "Sorry couldn't book vehicle at the moment",
            "Application Error"
          );
          console.error(res.statusText);
        }
      });
    } else {
      showErrorToUser(
        "Please select start and destination locations",
        "Input Error"
      );
    }
  });

  start_jny.addEventListener("click", () => {
    if (!journeyStarted) {
      fetch("/api/startJourney").then((res) => {
        if (res.ok) {
          journeyStarted = true;
          updateUI();
        }
      });
    } else if (!journeyEnded) {
      fetch("/api/endJourney").then((res) => {
        if (res.ok) {
          journeyEnded = true;
          updateUI();
        }
      });
    }
  });

  const set_map_start = document.getElementById("btn_select_map_start");
  set_map_start.addEventListener("click", () => {
    choosingStart = !choosingStart;
    choosingDest = false;

    if (choosingStart) {
      set_map_start.innerHTML = '<i class="bi bi-check-lg"></i>';
      set_map_dest.innerHTML = '<i class="bi bi-pin-map-fill"></i>';
    } else {
      set_map_start.innerHTML = '<i class="bi bi-pin-map-fill"></i>';
    }
  });

  const set_map_dest = document.getElementById("btn_select_map_destination");
  set_map_dest.addEventListener("click", () => {
    choosingDest = !choosingDest;
    choosingStart = false;

    if (choosingDest) {
      set_map_dest.innerHTML = '<i class="bi bi-check-lg"></i>';
      set_map_start.innerHTML = '<i class="bi bi-pin-map-fill"></i>';
    } else {
      set_map_dest.innerHTML = '<i class="bi bi-pin-map-fill"></i>';
    }
  });

  const stars = document.querySelectorAll("#rating_stars i");
  stars.forEach((el, idx, arry) => {
    el.addEventListener("click", (e) => {
      start_rating = arry.length - idx;
      console.log(start_rating);
      for (let j = 0; j < idx; j++) {
        arry[j].classList.remove("bi-star-fill");
        arry[j].classList.add("bi-star");
      }

      for (let j = idx; j < arry.length; j++) {
        arry[j].classList.remove("bi-star");
        arry[j].classList.add("bi-star-fill");
      }
    });
  });

  const submit_rating = document.getElementById("submit_rating");
  submit_rating.addEventListener("click", (e) => {
    fetch(
      "/api/rateBooking?" + new URLSearchParams({ rating: start_rating / 5 })
    );
    resetUIState();
  });

  const cancel_rating = document.getElementById("cancel_rating");
  cancel_rating.addEventListener("click", (e) => {
    resetUIState();
  });

  const prev_journeys = document.getElementById("prev_journeys");
  prev_journeys.addEventListener("click", (e) => {
    viewPrevJourneys();
  });
}
