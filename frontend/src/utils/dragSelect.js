export function calculateRectangle(coordinates) {
  const x3 = Math.min(coordinates.x1, coordinates.x2)
  const x4 = Math.max(coordinates.x1, coordinates.x2)
  const y3 = Math.min(coordinates.y1, coordinates.y2)
  const y4 = Math.max(coordinates.y1, coordinates.y2)
  return {
    left: x3 + "px",
    top: y3 + "px",
    width: x4 - x3 + "px",
    height: y4 - y3 + "px",
  }
}

export function handleDragSelect(entityElements, coordinates) {
  const selectedEntities = new Set()
  entityElements.forEach((element) => {
    const elementRect = element.getBoundingClientRect()
    const maxX = Math.max(coordinates.x1, coordinates.x2)
    const minX = Math.min(coordinates.x1, coordinates.x2)
    const maxY = Math.max(coordinates.y1, coordinates.y2)
    const minY = Math.min(coordinates.y1, coordinates.y2)
    if (
      ((elementRect.top >= minY && elementRect.top <= maxY) ||
        (elementRect.bottom >= minY && elementRect.bottom <= maxY) ||
        (minY >= elementRect.top && minY <= elementRect.bottom)) &&
      ((elementRect.left >= minX && elementRect.left <= maxX) ||
        (elementRect.right >= minX && elementRect.right <= maxX) ||
        (minX >= elementRect.left && minX <= elementRect.right))
    ) {
      //element.classList.add("bg-gray-100", "border-gray-300");
      selectedEntities.add(element.id)
    } else {
      // element.classList.remove("bg-gray-100", "border-gray-300");
    }
  })
  return selectedEntities
}
