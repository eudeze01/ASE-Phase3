import * as Maps from "./initmaps.js";
import * as UI from "./user_ui.js";
import * as db from "./dbstub.js";

// document.BingKey = await fetch("/api/getBingKey").then(async (v) => v.json());
document.BingKey = await db.getBingKey();

UI.InitializeUI(Maps.mapObject, Maps);
