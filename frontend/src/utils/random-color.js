const colors = {
  blue: "#0000ff",
  cyan: "#00ffff",
  darkblue: "#00008b",
  darkcyan: "#008b8b",
  darkgrey: "#a9a9a9",
  darkkhaki: "#bdb76b",
  darksalmon: "#e9967a",
  darkviolet: "#9400d3",
  gold: "#ffd700",
  green: "#008000",
  lightblue: "#add8e6",
  lightgreen: "#90ee90",
  magenta: "#ff00ff",
  maroon: "#800000",
  navy: "#000080",
  orange: "#ffa500",
  pink: "#ffc0cb",
  purple: "#800080",
  red: "#ff0000",
  yellow: "#ffff00",
}

const colorArray = Object.values(colors)
export function getRandomColor() {
  const randomIndex = Math.floor(Math.random() * colorArray.length)
  return colorArray[randomIndex].trim()
}
