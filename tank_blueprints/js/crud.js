import {
  BlueprintStore,
  NAME_MAX,
  PART_KINDS,
  PART_NAMES,
  STORAGE_KEY,
  escapeHtml,
  filterBlueprints,
  moveItem,
} from "./BlueprintStore.js";

const store = new BlueprintStore(localStorage);

const form = document.querySelector("#form");
const nameInput = document.querySelector("#name");
const checks = [...document.querySelectorAll(".check input")];
const orderEl = document.querySelector("#order");
const tbody = document.querySelector("#blueprints tbody");
const search = document.querySelector("#search");
const filterParts = document.querySelector("#filter-parts");

let order = [];
let editId = null;
let draft = null;
let rowErrors = {};

function icons(parts) {
  return parts
    .map((kind) => `<span class="icon ${kind}" title="${PART_NAMES[kind]}"></span>`)
    .join(" → ");
}

function renderOrder() {
  orderEl.innerHTML = order.map((kind, index) => `
    <li>
      <span class="icon ${kind}"></span>${PART_NAMES[kind]}
      <button type="button" class="btn-up" data-index="${index}" ${index === 0 ? "disabled" : ""}>▲</button>
      <button type="button" class="btn-down" data-index="${index}" ${index === order.length - 1 ? "disabled" : ""}>▼</button>
    </li>
  `).join("");
  document.querySelector("#order-empty").hidden = order.length > 0;
  for (const box of checks) box.checked = order.includes(box.value);
}

function makeRow(bp, index) {
  return `
    <tr data-id="${bp.id}">
      <td>${index + 1}</td>
      <td>${escapeHtml(bp.name)}</td>
      <td>${bp.parts.length}</td>
      <td>${icons(bp.parts)}</td>
      <td class="actions">
        <button type="button" class="btn-edit" data-id="${bp.id}" title="Изменить">✎</button>
        <button type="button" class="btn-delete" data-id="${bp.id}" title="Удалить">✕</button>
      </td>
    </tr>
  `;
}

function makeEditRow(index) {
  const steps = draft.parts.map((kind, i) => `
    <li>
      <span class="icon ${kind}"></span>${PART_NAMES[kind]}
      <button type="button" class="btn-row-up" data-index="${i}" ${i === 0 ? "disabled" : ""}>▲</button>
      <button type="button" class="btn-row-down" data-index="${i}" ${i === draft.parts.length - 1 ? "disabled" : ""}>▼</button>
      <button type="button" class="btn-row-remove" data-index="${i}" title="Убрать">✕</button>
    </li>
  `).join("");
  const missing = PART_KINDS.filter((kind) => !draft.parts.includes(kind))
    .map((kind) => `<button type="button" class="btn-row-add" data-kind="${kind}">+ ${PART_NAMES[kind]}</button>`)
    .join(" ");
  return `
    <tr data-id="${editId}" class="editing">
      <td>${index + 1}</td>
      <td>
        <input name="name" value="${escapeHtml(draft.name)}" maxlength="${NAME_MAX}" required>
        <span class="error">${escapeHtml(rowErrors.name || "")}</span>
      </td>
      <td>${draft.parts.length}</td>
      <td>
        <ol class="order">${steps}</ol>
        ${missing}
        <span class="error">${escapeHtml(rowErrors.parts || "")}</span>
      </td>
      <td class="actions">
        <button type="button" class="btn-save" data-id="${editId}" title="Сохранить">✓</button>
        <button type="button" class="btn-cancel" data-id="${editId}" title="Отмена">✕</button>
      </td>
    </tr>
  `;
}

function renderTable() {
  const all = store.list();
  const shown = filterBlueprints(all, search.value, Number(filterParts.value));
  tbody.innerHTML = shown
    .map((bp, index) => (bp.id === editId ? makeEditRow(index) : makeRow(bp, index)))
    .join("");
  document.querySelector("#filter-val").textContent = filterParts.value;
  document.querySelector("#count").textContent = `${shown.length} / ${all.length}`;
  document.querySelector("#list-empty").hidden = shown.length > 0;
}

function showFormErrors(errors) {
  document.querySelector("#name-error").textContent = errors.name || "";
  document.querySelector("#parts-error").textContent = errors.parts || "";
}

function startEdit(id) {
  const bp = store.get(id);
  if (!bp) return;
  editId = id;
  draft = { name: bp.name, parts: bp.parts.slice() };
  rowErrors = {};
  renderTable();
  tbody.querySelector("tr.editing input").focus();
}

function cancelEdit() {
  editId = null;
  draft = null;
  rowErrors = {};
  renderTable();
}

function saveEdit() {
  const result = store.validate(draft.name, draft.parts, editId);
  if (!result.valid) {
    rowErrors = result.errors;
    renderTable();
    return;
  }
  store.update(editId, draft.name, draft.parts);
  cancelEdit();
}

function confirmDelete(id) {
  const bp = store.get(id);
  if (!bp || !confirm(`Удалить чертёж «${bp.name}»?`)) return;
  store.remove(id);
  if (editId === id) cancelEdit();
  renderTable();
}

tbody.addEventListener("input", (e) => {
  if (draft && e.target.name === "name") draft.name = e.target.value;
});

tbody.addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const id = btn.dataset.id;
  const index = Number(btn.dataset.index);
  if (btn.classList.contains("btn-edit")) startEdit(id);
  else if (btn.classList.contains("btn-delete")) confirmDelete(id);
  else if (btn.classList.contains("btn-save")) saveEdit();
  else if (btn.classList.contains("btn-cancel")) cancelEdit();
  else if (btn.classList.contains("btn-row-up")) draft.parts = moveItem(draft.parts, index, -1);
  else if (btn.classList.contains("btn-row-down")) draft.parts = moveItem(draft.parts, index, 1);
  else if (btn.classList.contains("btn-row-remove")) draft.parts.splice(index, 1);
  else if (btn.classList.contains("btn-row-add")) draft.parts.push(btn.dataset.kind);
  if (btn.className.startsWith("btn-row")) renderTable();
});

orderEl.addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const index = Number(btn.dataset.index);
  order = moveItem(order, index, btn.classList.contains("btn-up") ? -1 : 1);
  renderOrder();
});

for (const box of checks) {
  box.addEventListener("change", () => {
    if (box.checked) order.push(box.value);
    else order = order.filter((kind) => kind !== box.value);
    renderOrder();
  });
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = new FormData(form);
  const result = store.validate(data.get("name"), order);
  showFormErrors(result.errors);
  if (!result.valid) return;
  store.create(data.get("name"), order);
  form.reset();
  order = [];
  renderOrder();
  renderTable();
});

search.addEventListener("input", renderTable);
filterParts.addEventListener("input", renderTable);

addEventListener("storage", (e) => {
  if (e.key !== STORAGE_KEY) return;
  store.items = store.load();
  renderTable();
});

renderOrder();
renderTable();
