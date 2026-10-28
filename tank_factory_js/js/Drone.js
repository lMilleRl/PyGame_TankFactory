/** Дрон-сборщик: не больше одной детали. */
export class Drone {
  constructor(gridX, gridY, carriedPart = null) {
    this.gridX = gridX;
    this.gridY = gridY;
    this.carriedPart = carriedPart;
  }

  get position() {
    return [this.gridX, this.gridY];
  }
}
