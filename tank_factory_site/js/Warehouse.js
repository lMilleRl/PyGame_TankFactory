export const WAREHOUSE_KEY = "tankFactory.warehouse";

export class Warehouse {
  constructor(storage) {
    this.storage = storage;
    this.tanks = this.load();
  }

  load() {
    try {
      const data = JSON.parse(this.storage.getItem(WAREHOUSE_KEY) || "[]");
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  }

  save() {
    this.storage.setItem(WAREHOUSE_KEY, JSON.stringify(this.tanks));
  }

  add(name, parts, turns, date = new Date()) {
    const tank = {
      number: this.tanks.length + 1,
      name,
      parts: parts.slice(),
      turns,
      date: date.toISOString(),
    };
    this.tanks.push(tank);
    this.save();
    return tank;
  }

  countByName() {
    const result = {};
    for (const tank of this.tanks) {
      result[tank.name] = (result[tank.name] || 0) + 1;
    }
    return result;
  }

  clear() {
    this.tanks = [];
    this.save();
  }
}
