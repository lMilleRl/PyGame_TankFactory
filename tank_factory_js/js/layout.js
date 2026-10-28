/** Разбор factory_layout.txt (те же символы, что в Python). */

const DIRS = {
  C: [1, 0],
  ">": [1, 0],
  "<": [-1, 0],
  "^": [0, -1],
  v: [0, 1],
};

const PARTS = { H: "chassis", B: "turret", N: "cannon" };
const GRID = new Set([...Object.keys(DIRS), ...Object.keys(PARTS), "#", ".", "D", "S"]);

export function parseLayoutText(text) {
  const gridRows = [];
  const overlays = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line === "#" || line.startsWith("# ")) continue;
    if (line.toUpperCase().startsWith("PART ")) {
      const bits = line.split(/\s+/);
      if (bits.length !== 4) throw new Error(`Неверный PART: ${raw}`);
      const kind = PARTS[bits[1].toUpperCase()];
      if (!kind) throw new Error(`Деталь ${bits[1]}`);
      overlays.push({ kind, gridX: Number(bits[2]), gridY: Number(bits[3]) });
      continue;
    }
    if ([...line].every((ch) => GRID.has(ch)) && line.length >= 3) {
      gridRows.push(line);
      continue;
    }
    throw new Error(`Строка уровня: ${raw}`);
  }
  if (!gridRows.length) throw new Error("Пустая сетка");
  const columns = gridRows[0].length;
  const rows = gridRows.length;
  if (gridRows.some((r) => r.length !== columns)) throw new Error("Разная длина строк");

  const walls = [];
  const conveyors = [];
  const parts = [];
  let droneStart = null;
  let assemblyPosition = null;

  gridRows.forEach((row, y) => {
    [...row].forEach((ch, x) => {
      if (ch === "#") walls.push([x, y]);
      else if (ch === "D") droneStart = [x, y];
      else if (ch === "S") assemblyPosition = [x, y];
      else if (DIRS[ch]) {
        const [dx, dy] = DIRS[ch];
        conveyors.push({ gridX: x, gridY: y, directionX: dx, directionY: dy });
      } else if (PARTS[ch]) {
        parts.push({ kind: PARTS[ch], gridX: x, gridY: y });
      }
    });
  });
  for (const p of overlays) parts.push(p);
  if (!droneStart) throw new Error("Нет D");
  if (!assemblyPosition) throw new Error("Нет S");
  return { columns, rows, walls, conveyors, parts, droneStart, assemblyPosition };
}
