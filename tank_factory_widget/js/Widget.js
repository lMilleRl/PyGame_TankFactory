import { FactoryGrid } from "../../tank_factory_js/js/FactoryGrid.js";
import { PartStack } from "../../tank_factory_js/js/PartStack.js";
import { createBoard, KEY_DIRS } from "./board.js";

export class Widget {
  constructor(gridEl, piecesEl, layoutText) {
    this.board = createBoard(gridEl, piecesEl);
    this.layoutText = layoutText;
    this.order = null;
    this.factory = null;
    this.lastOk = true;
    this.onChange = null;
  }

  reset(order = this.order) {
    this.order = order;
    this.factory = FactoryGrid.fromLayoutText(this.layoutText);
    if (order) this.factory.stack = new PartStack(order);
    this.lastOk = true;
    this.board.build(this.factory);
    this.changed();
  }

  move(dx, dy) {
    this.lastOk = this.factory.moveDrone(dx, dy);
    this.board.update(this.factory);
    this.changed();
  }

  interact() {
    this.lastOk = this.factory.interact();
    this.board.update(this.factory);
    this.changed();
  }

  handleKey(key) {
    if (KEY_DIRS[key]) {
      this.move(KEY_DIRS[key][0], KEY_DIRS[key][1]);
      return true;
    }
    if (key === " ") {
      this.interact();
      return true;
    }
    if (key === "r") {
      this.reset();
      return true;
    }
    return false;
  }

  attachKeyboard(target = window) {
    target.addEventListener("keydown", (e) => {
      if (e.repeat || !this.factory) return;
      if (["INPUT", "SELECT", "TEXTAREA"].includes(e.target.tagName)) return;
      if (this.handleKey(e.key.toLowerCase())) e.preventDefault();
    });
  }

  changed() {
    if (this.onChange) this.onChange(this.factory, this.lastOk);
  }
}
