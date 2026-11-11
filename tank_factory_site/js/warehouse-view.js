import { PART_NAMES, escapeHtml } from "../../tank_blueprints/js/BlueprintStore.js";
import { WAREHOUSE_KEY } from "./Warehouse.js";

export function renderWarehouse(warehouse, limit = Infinity) {
  const tanks = warehouse.tanks;
  document.querySelector("#store-total").textContent = String(tanks.length);
  document.querySelector("#store-empty").hidden = tanks.length > 0;

  const counts = warehouse.countByName();
  document.querySelector("#store-groups").innerHTML = Object.keys(counts)
    .map((name) => `<li>${escapeHtml(name)}: ${counts[name]} шт.</li>`)
    .join("");

  const rows = tanks.slice().reverse().slice(0, limit);
  document.querySelector("#store-list").innerHTML = rows.map((tank) => {
    const date = new Date(tank.date).toLocaleDateString("ru-RU");
    const parts = tank.parts.map((kind) => PART_NAMES[kind]).join(", ");
    return `<li><b>№${tank.number}</b> ${escapeHtml(tank.name)} <span>${parts} · ${tank.turns} ходов · ${date}</span></li>`;
  }).join("");
}

export function initWarehouse(warehouse, limit) {
  renderWarehouse(warehouse, limit);
  document.querySelector("#store-clear").addEventListener("click", () => {
    if (!confirm("Очистить склад?")) return;
    warehouse.clear();
    renderWarehouse(warehouse, limit);
  });
  addEventListener("storage", (e) => {
    if (e.key !== WAREHOUSE_KEY) return;
    warehouse.tanks = warehouse.load();
    renderWarehouse(warehouse, limit);
  });
}
