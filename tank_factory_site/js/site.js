import { startGame } from "./widget-integration.js";
import { Warehouse } from "./Warehouse.js";
import { initWarehouse } from "./warehouse-view.js";

const burger = document.querySelector("#burger");
const mobileMenu = document.querySelector("#mobile-menu");

burger.addEventListener("click", () => {
  mobileMenu.classList.toggle("open");
  burger.setAttribute("aria-expanded", mobileMenu.classList.contains("open"));
});

for (const link of mobileMenu.querySelectorAll("a")) {
  link.addEventListener("click", () => mobileMenu.classList.remove("open"));
}

const page = document.body.dataset.page;
if (page === "main") {
  startGame();
} else if (page === "warehouse") {
  initWarehouse(new Warehouse(localStorage));
}
