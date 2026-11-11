export const STORAGE_KEY = "tankFactory.blueprints";
export const PART_KINDS = ["chassis", "turret", "cannon"];
export const PART_NAMES = { chassis: "шасси", turret: "башня", cannon: "орудие" };
export const NAME_MAX = 40;

export function generateId() {
  return crypto.randomUUID();
}

export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export class BlueprintStore {
  constructor(storage) {
    this.storage = storage;
    this.items = this.load();
  }

  load() {
    const raw = this.storage.getItem(STORAGE_KEY);
    if (raw === null) {
      this.items = [{ id: generateId(), name: "Т-19 базовый", parts: ["chassis", "turret", "cannon"] }];
      this.save();
      return this.items;
    }
    try {
      const data = JSON.parse(raw);
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  }

  save() {
    this.storage.setItem(STORAGE_KEY, JSON.stringify(this.items));
  }

  list() {
    return this.items.slice();
  }

  get(id) {
    return this.items.find((bp) => bp.id === id) || null;
  }

  validate(name, parts, id = null) {
    const errors = {};
    const clean = String(name).trim();
    if (!clean) {
      errors.name = "Введите название танка";
    } else if (clean.length > NAME_MAX) {
      errors.name = `Не длиннее ${NAME_MAX} символов`;
    } else if (this.items.some((bp) => bp.id !== id && bp.name.toLowerCase() === clean.toLowerCase())) {
      errors.name = "Чертёж с таким названием уже есть";
    }

    if (!Array.isArray(parts) || parts.length === 0) {
      errors.parts = "Выберите хотя бы одну деталь";
    } else if (parts.some((kind) => !PART_KINDS.includes(kind))) {
      errors.parts = "Неизвестная деталь";
    } else if (new Set(parts).size !== parts.length) {
      errors.parts = "Детали в чертеже не должны повторяться";
    }

    return { valid: Object.keys(errors).length === 0, errors, name: clean };
  }

  check(name, parts, id) {
    const result = this.validate(name, parts, id);
    if (!result.valid) {
      throw new Error(result.errors.name || result.errors.parts);
    }
    return result.name;
  }

  create(name, parts) {
    const blueprint = { id: generateId(), name: this.check(name, parts, null), parts: parts.slice() };
    this.items.push(blueprint);
    this.save();
    return blueprint;
  }

  update(id, name, parts) {
    const blueprint = this.get(id);
    if (!blueprint) throw new Error("Чертёж не найден");
    blueprint.name = this.check(name, parts, id);
    blueprint.parts = parts.slice();
    this.save();
    return blueprint;
  }

  remove(id) {
    const before = this.items.length;
    this.items = this.items.filter((bp) => bp.id !== id);
    if (this.items.length === before) return false;
    this.save();
    return true;
  }
}

export function moveItem(list, index, step) {
  const target = index + step;
  if (target < 0 || target >= list.length) return list.slice();
  const copy = list.slice();
  const [item] = copy.splice(index, 1);
  copy.splice(target, 0, item);
  return copy;
}

export function filterBlueprints(items, text, maxParts) {
  const query = text.trim().toLowerCase();
  return items.filter((bp) => bp.parts.length <= maxParts && bp.name.toLowerCase().includes(query));
}
