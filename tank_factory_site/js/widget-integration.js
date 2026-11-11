import { Widget } from "../../tank_factory_widget/js/Widget.js";
import { BlueprintStore, PART_NAMES, STORAGE_KEY } from "../../tank_blueprints/js/BlueprintStore.js";
import { CURRENT_KEY, DEFAULT_NAME, orderFor, pickCurrent } from "./blueprint.js";
import { renderHotbar, renderSteps } from "./hotbar.js";
import { updateHud } from "./hud.js";
import { Warehouse } from "./Warehouse.js";
import { renderWarehouse, initWarehouse } from "./warehouse-view.js";

const STORE_LIMIT = 6;

export async function startGame() {
  const res = await fetch("../factory_layout.txt");
  const layoutText = await res.text();

  const store = new BlueprintStore(localStorage);
  const warehouse = new Warehouse(localStorage);
  const widget = new Widget(document.querySelector("#grid"), document.querySelector("#pieces"), layoutText);
  const hotbar = document.querySelector("#hotbar");

  let current = pickCurrent(store.list(), localStorage);
  let shownFactory = null;
  let stored = false;

  function title() {
    return current ? current.name : DEFAULT_NAME;
  }

  function drawHotbar() {
    renderHotbar(hotbar, store.list(), current ? current.id : "", warehouse.countByName());
  }

  widget.onChange = (factory, lastOk) => {
    if (factory !== shownFactory) {
      shownFactory = factory;
      stored = false;
    }
    if (factory.status === "won" && !stored) {
      warehouse.add(title(), factory.stack.order, factory.turnCount);
      stored = true;
      factory.message = `Танк «${title()}» отправлен на склад`;
      renderWarehouse(warehouse, STORE_LIMIT);
      drawHotbar();
    }
    updateHud(factory, lastOk, PART_NAMES);
    document.querySelector("#bp-name").textContent = title();
    document.querySelector("#hud-bp").textContent = title();
    renderSteps(document.querySelector("#bp-steps"), factory);
  };

  function select(id) {
    if (id) localStorage.setItem(CURRENT_KEY, id);
    else localStorage.removeItem(CURRENT_KEY);
    current = pickCurrent(store.list(), localStorage);
    drawHotbar();
    widget.reset(orderFor(current));
  }

  hotbar.addEventListener("click", (e) => {
    const card = e.target.closest(".card");
    if (card) select(card.dataset.id);
  });

  for (const btn of document.querySelectorAll(".pad button")) {
    btn.addEventListener("click", () => widget.handleKey(btn.dataset.key));
  }
  document.querySelector("#restart").addEventListener("click", () => widget.reset());

  addEventListener("storage", (e) => {
    if (e.key !== STORAGE_KEY && e.key !== CURRENT_KEY) return;
    store.items = store.load();
    const fresh = pickCurrent(store.list(), localStorage);
    const changed = JSON.stringify(fresh) !== JSON.stringify(current);
    current = fresh;
    drawHotbar();
    if (changed) widget.reset(orderFor(current));
  });

  widget.attachKeyboard();
  initWarehouse(warehouse, STORE_LIMIT);
  drawHotbar();
  widget.reset(orderFor(current));
}
