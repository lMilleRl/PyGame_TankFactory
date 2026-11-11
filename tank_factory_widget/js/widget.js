import { Widget } from "./Widget.js";

const PART_NAMES = { chassis: "шасси", turret: "башня", cannon: "орудие" };

function updateHud(factory) {
  const names = { active: "игра", won: "победа" };
  document.querySelector("#status").textContent = names[factory.status] || factory.status;
  document.querySelector("#turns").textContent = String(factory.turnCount);
  document.querySelector("#needed").textContent = factory.stack.required
    ? PART_NAMES[factory.stack.required]
    : "-";
  document.querySelector("#stack").textContent = factory.stack.items.length
    ? factory.stack.items.map((name) => PART_NAMES[name]).join(", ")
    : "-";
  document.querySelector("#message").textContent = factory.message;
  document.querySelector("#result").hidden = factory.status !== "won";
}

async function start() {
  const res = await fetch("../factory_layout.txt");
  const widget = new Widget(document.querySelector("#grid"), document.querySelector("#pieces"), await res.text());
  widget.onChange = updateHud;
  widget.attachKeyboard();
  widget.reset();
  window.TankFactory = widget;
}

start();
