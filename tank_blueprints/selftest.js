import {
  BlueprintStore,
  STORAGE_KEY,
  escapeHtml,
  filterBlueprints,
  moveItem,
} from "./js/BlueprintStore.js";

let passed = 0;
let failed = 0;

function check(name, cond) {
  if (cond) {
    console.log(`OK  ${name}`);
    passed += 1;
  } else {
    console.log(`FAIL ${name}`);
    failed += 1;
  }
}

function throws(fn) {
  try {
    fn();
    return false;
  } catch {
    return true;
  }
}

class MemoryStorage {
  constructor() {
    this.data = {};
  }

  getItem(key) {
    return key in this.data ? this.data[key] : null;
  }

  setItem(key, value) {
    this.data[key] = String(value);
  }

  removeItem(key) {
    delete this.data[key];
  }
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

const storage = new MemoryStorage();
const store = new BlueprintStore(storage);

check("1 default blueprint", store.list().length === 1);
check("2 default saved at once", JSON.parse(storage.getItem(STORAGE_KEY)).length === 1);
check("3 default order", store.list()[0].parts.join(",") === "chassis,turret,cannon");

const light = store.create("Лёгкий разведчик", ["chassis", "turret"]);
check("4 id is UUID v4", UUID.test(light.id));
check("5 saved to storage", JSON.parse(storage.getItem(STORAGE_KEY)).length === 2);

check("6 empty name error", store.validate("   ", ["chassis"]).errors.name === "Введите название танка");
check("7 long name error", store.validate("x".repeat(41), ["chassis"]).valid === false);
check("8 no parts error", store.validate("Пустой", []).errors.parts !== undefined);
check("9 repeated part error", store.validate("Двойной", ["chassis", "chassis"]).valid === false);
check("10 unknown part error", store.validate("Странный", ["wing"]).valid === false);
check("11 same name error", store.validate("лёгкий разведчик", ["chassis"]).valid === false);
check("12 two errors at once", Object.keys(store.validate("", []).errors).length === 2);
check("13 create throws on bad data", throws(() => store.create("", ["chassis"])));

const heavy = store.create("Тяжёлый", ["cannon", "chassis", "turret"]);
check("14 strict order kept", store.get(heavy.id).parts.join(",") === "cannon,chassis,turret");
check("15 ids differ", heavy.id !== light.id);

store.update(heavy.id, "Тяжёлый", ["chassis", "cannon", "turret"]);
check("16 update order", store.get(heavy.id).parts.join(",") === "chassis,cannon,turret");
check("17 update keeps own name", !throws(() => store.update(heavy.id, "Тяжёлый", ["chassis"])));
check("18 update to taken name", throws(() => store.update(heavy.id, "Т-19 базовый", ["chassis"])));
check("19 update missing id", throws(() => store.update("nope", "Нет", ["chassis"])));

const again = new BlueprintStore(storage);
check("20 reload from storage", again.list().length === 3 && again.get(heavy.id).parts.join(",") === "chassis");

check("21 remove", store.remove(light.id) === true && store.get(light.id) === null);
check("22 remove missing", store.remove(light.id) === false);
check("23 removed in storage", new BlueprintStore(storage).list().length === 2);

check("24 move up", moveItem(["a", "b", "c"], 2, -1).join(",") === "a,c,b");
check("25 move down", moveItem(["a", "b", "c"], 0, 1).join(",") === "b,a,c");
check("26 move out of range", moveItem(["a", "b"], 0, -1).join(",") === "a,b");

const sample = [
  { id: "1", name: "Т-19 базовый", parts: ["chassis", "turret", "cannon"] },
  { id: "2", name: "Разведчик", parts: ["chassis", "turret"] },
  { id: "3", name: "Самоходка", parts: ["chassis", "cannon"] },
];
check("27 filter by parts count", filterBlueprints(sample, "", 2).length === 2);
check("28 search by name", filterBlueprints(sample, "разв", 3).map((bp) => bp.id).join() === "2");
check("29 search and filter", filterBlueprints(sample, "т-19", 2).length === 0);

check("30 escapeHtml tags", escapeHtml("<img src=x onerror=alert(1)>") === "&lt;img src=x onerror=alert(1)&gt;");
check("31 escapeHtml quotes", escapeHtml(`"a" & 'b'`) === "&quot;a&quot; &amp; &#39;b&#39;");

storage.setItem(STORAGE_KEY, "{broken");
check("32 broken JSON gives empty list", new BlueprintStore(storage).list().length === 0);

storage.setItem(STORAGE_KEY, "[]");
check("33 empty saved list stays empty", new BlueprintStore(storage).list().length === 0);

console.log(`\nИтого: ${passed} OK, ${failed} FAIL`);
if (failed > 0) process.exit(1);
