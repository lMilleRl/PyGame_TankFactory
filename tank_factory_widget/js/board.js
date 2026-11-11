function conveyorClass(dx, dy) {
  if (dx === 1) return "conveyor-right";
  if (dx === -1) return "conveyor-left";
  if (dy === -1) return "conveyor-up";
  return "conveyor-down";
}

function setPos(el, gx, gy) {
  el.style.transform = `translate(${gx * 100}%, ${gy * 100}%)`;
}

export function createBoard(gridEl, piecesEl) {
  const parts = {};
  let drone = null;
  let carry = null;

  function build(factory) {
    gridEl.innerHTML = "";
    piecesEl.innerHTML = "";
    for (let y = 0; y < factory.rows; y += 1) {
      for (let x = 0; x < factory.columns; x += 1) {
        const cell = document.createElement("div");
        const names = ["cell"];
        if (factory.walls.has(factory.key(x, y))) {
          names.push("wall");
        } else {
          names.push("floor");
          const conv = factory.conveyors.get(factory.key(x, y));
          if (conv) names.push(conveyorClass(conv.directionX, conv.directionY));
          if (x === factory.assemblyPosition[0] && y === factory.assemblyPosition[1]) {
            names.push("assembly");
          }
        }
        cell.className = names.join(" ");
        gridEl.appendChild(cell);
      }
    }

    for (const kind of Object.keys(parts)) delete parts[kind];
    for (const part of factory.parts) {
      const el = document.createElement("div");
      el.className = `piece ${part.kind}`;
      piecesEl.appendChild(el);
      parts[part.kind] = el;
    }
    drone = document.createElement("div");
    drone.className = "piece drone";
    carry = document.createElement("div");
    carry.className = "carry";
    drone.appendChild(carry);
    piecesEl.appendChild(drone);
    update(factory);
  }

  function update(factory) {
    for (const kind of Object.keys(parts)) {
      const part = factory.parts.find((item) => item.kind === kind);
      if (part) {
        parts[kind].style.display = "";
        setPos(parts[kind], part.gridX, part.gridY);
      } else {
        parts[kind].style.display = "none";
      }
    }
    setPos(drone, factory.drone.gridX, factory.drone.gridY);
    const carried = factory.drone.carriedPart;
    carry.className = carried ? `carry on ${carried.kind}` : "carry";
  }

  return { build, update };
}

export const KEY_DIRS = {
  arrowup: [0, -1],
  arrowdown: [0, 1],
  arrowleft: [-1, 0],
  arrowright: [1, 0],
};
