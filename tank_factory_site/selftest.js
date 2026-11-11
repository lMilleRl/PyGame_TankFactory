import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { FactoryGrid } from "../tank_factory_js/js/FactoryGrid.js";
import { BlueprintStore } from "../tank_blueprints/js/BlueprintStore.js";
import { Warehouse } from "./js/Warehouse.js";
import { PartStack } from "../tank_factory_js/js/PartStack.js";
import { CURRENT_KEY, orderFor, pickCurrent } from "./js/blueprint.js";
import { hudState } from "./js/hud.js";
import { cardStats } from "./js/hotbar.js";

function applyBlueprint(factory, blueprint) {
  factory.stack = new PartStack(orderFor(blueprint));
  return factory;
}

let passed = 0;
let failed = 0;

function check(name, cond) {
  if (cond) {
    console.log(`OK  ${name}`);
    passed += 1;
  } else {
    console.log(`FAIL ${name}`);
    failed += 1;
  }
}

class MemoryStorage {
  constructor() {
    this.data = {};
  }

  getItem(key) {
    return key in this.data ? this.data[key] : null;
  }

  setItem(key, value) {
    this.data[key] = String(value);
  }

  removeItem(key) {
    delete this.data[key];
  }
}

const storage = new MemoryStorage();
const store = new BlueprintStore(storage);
const scout = store.create("Разведчик", ["chassis", "turret"]);

check("1 no current blueprint", pickCurrent(store.list(), storage) === null);
storage.setItem(CURRENT_KEY, scout.id);
check("2 current from storage", pickCurrent(store.list(), storage).name === "Разведчик");
storage.setItem(CURRENT_KEY, "нет-такого-id");
check("3 missing id gives default", pickCurrent(store.list(), storage) === null);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const layoutText = fs.readFileSync(path.resolve(__dirname, "../factory_layout.txt"), "utf8");

const plain = applyBlueprint(FactoryGrid.fromLayoutText(layoutText), null);
check("4 default order", plain.stack.order.join(",") === "chassis,turret,cannon");

const custom = applyBlueprint(FactoryGrid.fromLayoutText(layoutText), scout);
check("5 blueprint order", custom.stack.order.join(",") === "chassis,turret");

const small = applyBlueprint(new FactoryGrid({
  columns: 6,
  rows: 6,
  droneStart: [1, 1],
  assemblyPosition: [1, 1],
  parts: [
    { kind: "chassis", gridX: 1, gridY: 1 },
    { kind: "turret", gridX: 2, gridY: 1 },
  ],
}), scout);
small.interact();
small.interact();
check("6 chassis placed", small.stack.items.join(",") === "chassis" && small.status === "active");
small.drone.gridX = 2;
small.interact();
small.drone.gridX = 1;
small.interact();
check("7 win after two parts", small.status === "won");

const reversed = applyBlueprint(new FactoryGrid({
  columns: 6,
  rows: 6,
  droneStart: [1, 1],
  assemblyPosition: [1, 1],
  parts: [{ kind: "chassis", gridX: 1, gridY: 1 }],
}), { id: "x", name: "Обратный", parts: ["cannon", "turret", "chassis"] });
reversed.interact();
check("8 wrong first part rejected", reversed.interact() === false && reversed.stack.items.length === 0);

const warehouse = new Warehouse(storage);
check("9 empty warehouse", warehouse.tanks.length === 0);
warehouse.add("Разведчик", ["chassis", "turret"], 14, new Date("2026-11-11T10:00:00Z"));
warehouse.add("Разведчик", ["chassis", "turret"], 12);
warehouse.add("Т-19 базовый", ["chassis", "turret", "cannon"], 30);
check("10 numbers go up", warehouse.tanks.map((t) => t.number).join(",") === "1,2,3");
check("11 count by name", warehouse.countByName()["Разведчик"] === 2);
check("12 saved and reloaded", new Warehouse(storage).tanks.length === 3);
check("13 date saved as text", new Warehouse(storage).tanks[0].date === "2026-11-11T10:00:00.000Z");
warehouse.clear();
check("14 clear", new Warehouse(storage).tanks.length === 0);

storage.setItem("tankFactory.warehouse", "oops");
check("15 broken warehouse is empty", new Warehouse(storage).tanks.length === 0);

const hud = applyBlueprint(FactoryGrid.fromLayoutText(layoutText), null);
check("16 hud start is low", hudState(hud, true).cls === "low" && hudState(hud, true).level === 0);
check("17 hud alert after refusal", hudState(hud, false).cls === "alert");
hud.stack.push("chassis");
check("18 hud mid after one of three", hudState(hud, true).cls === "mid");
hud.stack.push("turret");
check("19 hud high after two of three", hudState(hud, true).cls === "high");
hud.status = "won";
check("20 hud done on win", hudState(hud, false).cls === "done" && hudState(hud, true).level === 1);
check("21 default order is a copy", orderFor(null) !== orderFor(null) && orderFor(scout).join(",") === "chassis,turret");
check("22 card stats text", cardStats(["chassis", "turret"], 2) === "деталей: 2 · на складе: 2");

console.log(`\nИтого: ${passed} OK, ${failed} FAIL`);
if (failed > 0) process.exit(1);
