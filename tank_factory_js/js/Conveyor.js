/** Клетка конвейера с единичным вектором сдвига. */
export class Conveyor {
  constructor(gridX, gridY, directionX, directionY) {
    if (Math.abs(directionX) + Math.abs(directionY) !== 1) {
      throw new Error("Вектор конвейера должен вести ровно на одну клетку");
    }
    this.gridX = gridX;
    this.gridY = gridY;
    this.directionX = directionX;
    this.directionY = directionY;
  }

  get position() {
    return [this.gridX, this.gridY];
  }

  destination() {
    return [this.gridX + this.directionX, this.gridY + this.directionY];
  }
}
