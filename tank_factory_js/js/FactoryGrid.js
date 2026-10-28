import { Conveyor } from "./Conveyor.js";
import { Drone } from "./Drone.js";
import { PartStack } from "./PartStack.js";
import { parseLayoutText } from "./layout.js";

const PART_NAMES = { chassis: "шасси", turret: "башня", cannon: "орудие" };

/** Дискретная сетка цеха: ход дрона, конвейеры, сборка. */
export class FactoryGrid {
  constructor({
    columns = 10,
    rows = 10,
    droneStart = [1, 1],
    assemblyPosition = [4, 4],
    parts = [],
    conveyors = [],
    walls = [],
  } = {}) {
    this.columns = columns;
    this.rows = rows;
    this.drone = new Drone(droneStart[0], droneStart[1]);
    this.assemblyPosition = assemblyPosition.slice();
    this.parts = parts.map((p) => ({ kind: p.kind, gridX: p.gridX, gridY: p.gridY }));
    this.conveyors = new Map();
    for (const c of conveyors) {
      const key = `${c.gridX},${c.gridY}`;
      this.conveyors.set(key, new Conveyor(c.gridX, c.gridY, c.directionX, c.directionY));
    }
    this.walls = new Set(walls.map(([x, y]) => `${x},${y}`));
    this.stack = new PartStack();
    this.turnCount = 0;
    this.status = "active";
    this.message = "Готово к сборке";
    // Пошаговый «таймер»: каждый успешный ход увеличивает turnCount.
  }

  static fromLayoutText(text) {
    const layout = parseLayoutText(text);
    return new FactoryGrid(layout);
  }

  static fromLayoutFile(fileText) {
    try {
      return FactoryGrid.fromLayoutText(fileText);
    } catch (err) {
      throw new Error(`Ошибка уровня: ${err.message}`);
    }
  }

  key(x, y) {
    return `${x},${y}`;
  }

  inside(x, y) {
    return x >= 0 && y >= 0 && x < this.columns && y < this.rows;
  }

  getPartAt(x, y) {
    return this.parts.find((p) => p.gridX === x && p.gridY === y) || null;
  }

  moveDrone(dx, dy) {
    if (this.status === "won") return false;
    if (Math.abs(dx) + Math.abs(dy) !== 1) {
      throw new Error("За шаг можно пройти только одну клетку");
    }
    const nx = this.drone.gridX + dx;
    const ny = this.drone.gridY + dy;
    if (!this.inside(nx, ny) || this.walls.has(this.key(nx, ny))) {
      this.message = "Путь закрыт";
      return false;
    }
    this.drone.gridX = nx;
    this.drone.gridY = ny;
    this._finishTurn("Дрон сходил");
    return true;
  }

  interact() {
    if (this.status === "won") return false;
    if (!this.drone.carriedPart) {
      const part = this.getPartAt(this.drone.gridX, this.drone.gridY);
      if (!part) {
        this.message = "Нет детали";
        return false;
      }
      this.parts = this.parts.filter((p) => p !== part);
      this.drone.carriedPart = part;
      this._finishTurn(`Взял ${PART_NAMES[part.kind]}`);
      return true;
    }
    const part = this.drone.carriedPart;
    if (this.drone.gridX === this.assemblyPosition[0] && this.drone.gridY === this.assemblyPosition[1]) {
      if (!this.stack.push(part.kind)) {
        this.message = `Нужна деталь: ${PART_NAMES[this.stack.required]}`;
        return false;
      }
      this.drone.carriedPart = null;
      if (this.stack.isComplete()) {
        this.status = "won";
        this._finishTurn("Танк собран");
      } else {
        this._finishTurn(`Установлено: ${PART_NAMES[part.kind]}`);
      }
      return true;
    }
    if (this.getPartAt(this.drone.gridX, this.drone.gridY)) {
      this.message = "Клетка занята";
      return false;
    }
    part.gridX = this.drone.gridX;
    part.gridY = this.drone.gridY;
    this.parts.push(part);
    this.drone.carriedPart = null;
    this._finishTurn(`Положил ${PART_NAMES[part.kind]}`);
    return true;
  }

  _finishTurn(message) {
    this.turnCount += 1;
    const moved = this._advanceConveyors();
    this.message = moved ? `${message}. Конвейер сдвинул: ${moved}` : message;
  }

  _advanceConveyors() {
    const positions = this.parts.map((p) => this.key(p.gridX, p.gridY));
    const intended = new Map();
    this.parts.forEach((part, index) => {
      const conv = this.conveyors.get(this.key(part.gridX, part.gridY));
      if (!conv) return;
      const [dx, dy] = [conv.directionX, conv.directionY];
      const nx = part.gridX + dx;
      const ny = part.gridY + dy;
      if (this.inside(nx, ny) && !this.walls.has(this.key(nx, ny))) {
        intended.set(index, [nx, ny]);
      }
    });
    const destCount = new Map();
    for (const dest of intended.values()) {
      const k = this.key(dest[0], dest[1]);
      destCount.set(k, (destCount.get(k) || 0) + 1);
    }
    for (const [index, dest] of [...intended.entries()]) {
      if (destCount.get(this.key(dest[0], dest[1])) !== 1) intended.delete(index);
    }
    let changed = true;
    while (changed) {
      changed = false;
      const stationary = new Set(
        positions.filter((_, i) => !intended.has(i)),
      );
      for (const [index, dest] of [...intended.entries()]) {
        if (stationary.has(this.key(dest[0], dest[1]))) {
          intended.delete(index);
          changed = true;
        }
      }
    }
    for (const [index, dest] of intended.entries()) {
      this.parts[index].gridX = dest[0];
      this.parts[index].gridY = dest[1];
    }
    return intended.size;
  }
}
