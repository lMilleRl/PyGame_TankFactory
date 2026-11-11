import { PART_NAMES, escapeHtml } from "../../tank_blueprints/js/BlueprintStore.js";
import { DEFAULT_NAME, DEFAULT_ORDER } from "./blueprint.js";

function icons(parts) {
  return parts.map((kind) => `<span class="icon ${kind}" title="${PART_NAMES[kind]}"></span>`).join("");
}

export function cardStats(parts, inStore) {
  return `деталей: ${parts.length} · на складе: ${inStore}`;
}

export function renderHotbar(container, blueprints, selectedId, counts) {
  const cards = [{ id: "", name: DEFAULT_NAME, parts: DEFAULT_ORDER }, ...blueprints];
  container.innerHTML = cards.map((bp) => `
    <button type="button" class="card ${bp.id === (selectedId || "") ? "selected" : ""}" data-id="${bp.id}">
      <span class="card-name">${escapeHtml(bp.name)}</span>
      <span class="card-parts">${icons(bp.parts)}</span>
      <span class="card-stats">${escapeHtml(cardStats(bp.parts, counts[bp.name] || 0))}</span>
    </button>
  `).join("");
}

export function renderSteps(list, factory) {
  const done = factory.stack.items.length;
  list.innerHTML = factory.stack.order.map((kind, index) => {
    let cls = "";
    let state = "ожидает";
    if (index < done) {
      cls = "done";
      state = "готово";
    } else if (index === done && factory.status === "active") {
      cls = "next";
      state = "следующая";
    }
    return `<li class="${cls}"><span class="icon ${kind}"></span>${PART_NAMES[kind]}<span class="state">${state}</span></li>`;
  }).join("");
}
