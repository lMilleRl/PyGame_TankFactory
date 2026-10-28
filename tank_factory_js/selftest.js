import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { Conveyor } from "./js/Conveyor.js";
import { Drone } from "./js/Drone.js";
import { PartStack } from "./js/PartStack.js";
import { FactoryGrid } from "./js/FactoryGrid.js";
import { parseLayoutText } from "./js/layout.js";

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

const tiny = new FactoryGrid({
  columns: 6,
  rows: 6,
  droneStart: [1, 1],
  assemblyPosition: [4, 4],
  parts: [{ kind: "chassis", gridX: 2, gridY: 2 }],
  conveyors: [{ gridX: 2, gridY: 2, directionX: 1, directionY: 0 }],
  walls: [],
});

check("1 grid size", tiny.columns === 6 && tiny.rows === 6);
check("2 drone start", tiny.drone.gridX === 1 && tiny.drone.gridY === 1);
check("3 move one cell", tiny.moveDrone(1, 0) === true && tiny.drone.gridX === 2);
check("4 turn increments", tiny.turnCount === 1);
check("5 conveyor moved part", tiny.parts[0].gridX === 3 && tiny.parts[0].gridY === 2);

let diagOk = false;
try {
  tiny.moveDrone(1, 1);
} catch {
  diagOk = true;
}
check("6 diagonal rejected", diagOk);

const blocked = new FactoryGrid({
  columns: 5,
  rows: 5,
  droneStart: [1, 1],
  assemblyPosition: [3, 3],
  walls: [[2, 1]],
});
check("7 wall blocks without turn", blocked.moveDrone(1, 0) === false && blocked.turnCount === 0);

const stack = new PartStack();
check("8 stack required chassis", stack.required === "chassis");
check("9 reject wrong part", stack.push("turret") === false);
check("10 push chassis", stack.push("chassis") === true);
check("11 push turret", stack.push("turret") === true);
check("12 push cannon", stack.push("cannon") === true);
check("13 complete via join", stack.isComplete() === true);
check("14 indices 0,1,2", stack.indices.join(",") === "0,1,2");

const drone = new Drone(0, 0);
check("15 drone empty carry", drone.carriedPart === null);

let badConv = false;
try {
  new Conveyor(1, 1, 1, 1);
} catch {
  badConv = true;
}
check("16 bad conveyor vector", badConv);
check("17 conveyor dest", new Conveyor(2, 2, 0, 1).destination().join(",") === "2,3");

const assemble = new FactoryGrid({
  columns: 6,
  rows: 6,
  droneStart: [1, 1],
  assemblyPosition: [1, 1],
  parts: [
    { kind: "chassis", gridX: 1, gridY: 1 },
    { kind: "turret", gridX: 2, gridY: 1 },
    { kind: "cannon", gridX: 3, gridY: 1 },
  ],
});
check("18 pickup", assemble.interact() === true && assemble.drone.carriedPart.kind === "chassis");
check("19 place chassis", assemble.interact() === true && assemble.stack.items.length === 1);
assemble.drone.gridX = 2;
assemble.drone.gridY = 1;
assemble.interact();
assemble.drone.gridX = 1;
assemble.drone.gridY = 1;
check("20 place turret", assemble.interact() === true);
assemble.drone.gridX = 3;
assemble.drone.gridY = 1;
assemble.interact();
assemble.drone.gridX = 1;
assemble.drone.gridY = 1;
check("21 place cannon and win", assemble.interact() === true && assemble.status === "won");

const simultaneous = new FactoryGrid({
  columns: 6,
  rows: 6,
  droneStart: [1, 1],
  assemblyPosition: [4, 4],
  parts: [
    { kind: "chassis", gridX: 1, gridY: 2 },
    { kind: "turret", gridX: 2, gridY: 2 },
  ],
  conveyors: [
    { gridX: 1, gridY: 2, directionX: 1, directionY: 0 },
    { gridX: 2, gridY: 2, directionX: 1, directionY: 0 },
  ],
});
simultaneous.moveDrone(0, 1);
check(
  "22 simultaneous conveyors",
  simultaneous.parts[0].gridX === 2 && simultaneous.parts[1].gridX === 3,
);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const layoutPath = path.resolve(__dirname, "../factory_layout.txt");
const layoutText = fs.readFileSync(layoutPath, "utf8");
let parsedOk = true;
let parsed;
try {
  parsed = parseLayoutText(layoutText);
} catch (e) {
  parsedOk = false;
  console.log(e);
}
check("23 parse real layout", parsedOk && parsed.columns === 10 && parsed.rows === 10);
const fromFile = FactoryGrid.fromLayoutText(layoutText);
check("24 factory from layout has 3 parts", fromFile.parts.length === 3);
check("25 drone at D", fromFile.drone.gridX === 1 && fromFile.drone.gridY === 8);
fromFile.moveDrone(1, 0);
check("26 default parts move on conveyors", fromFile.parts.every((p) => p.gridX !== undefined));

let badLayout = false;
try {
  parseLayoutText("####\n#DZX#\n####\n");
} catch {
  badLayout = true;
}
check("27 bad layout throws", badLayout);

check("28 PartStack join format", new PartStack().order.join("-") === "chassis-turret-cannon");

console.log(`\nИтого: ${passed} OK, ${failed} FAIL`);
if (failed > 0) process.exit(1);
