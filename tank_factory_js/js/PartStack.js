/** Стек сборки: push и join для проверки порядка. */
export class PartStack {
  constructor(order = ["chassis", "turret", "cannon"]) {
    this.order = order.slice();
    this.items = [];
  }

  get required() {
    if (this.items.length >= this.order.length) return null;
    return this.order[this.items.length];
  }

  push(partKind) {
    if (partKind !== this.required) {
      return false;
    }
    this.items.push(partKind);
    return true;
  }

  isComplete() {
    return this.items.join(",") === this.order.join(",");
  }

  get indices() {
    return this.items.map((name) => this.order.indexOf(name));
  }
}
