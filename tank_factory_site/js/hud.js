export function hudState(factory, lastOk) {
  const total = factory.stack.order.length;
  const done = factory.stack.items.length;
  const level = total ? done / total : 0;
  if (factory.status === "won") return { level: 1, cls: "done", label: "танк собран" };
  if (!lastOk) return { level, cls: "alert", label: "отказ" };
  if (done === 0) return { level, cls: "low", label: "смена" };
  if (level < 0.6) return { level, cls: "mid", label: "сборка" };
  return { level, cls: "high", label: "почти готов" };
}

export function updateHud(factory, lastOk, partNames) {
  const state = hudState(factory, lastOk);
  const fill = document.querySelector("#meter-fill");
  fill.style.width = `${Math.round(state.level * 100)}%`;
  fill.className = `meter-fill ${state.cls}`;
  const status = document.querySelector("#status");
  status.textContent = state.label;
  status.className = `pill ${state.cls}`;
  document.querySelector("#meter-label").textContent =
    `${factory.stack.items.length} / ${factory.stack.order.length}`;
  document.querySelector("#turns").textContent = String(factory.turnCount);
  document.querySelector("#needed").textContent = factory.stack.required
    ? partNames[factory.stack.required]
    : "-";
  document.querySelector("#message").textContent = factory.message;
}
