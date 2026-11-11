export const CURRENT_KEY = "tankFactory.currentBlueprint";
export const DEFAULT_NAME = "Стандарт ЛР4";
export const DEFAULT_ORDER = ["chassis", "turret", "cannon"];

export function orderFor(blueprint) {
  return blueprint ? blueprint.parts.slice() : DEFAULT_ORDER.slice();
}

export function pickCurrent(blueprints, storage) {
  const id = storage.getItem(CURRENT_KEY);
  return blueprints.find((bp) => bp.id === id) || null;
}
