export function getIconUrl(file_type) {
  return new URL(
    `/src/assets/images/icons/${file_type.toLowerCase()}.svg`,
    import.meta.url
  )
}

export function getThumbnailUrl({ name, file_type, thumbnail, external }) {
  // Currently only Slides
  if (external) return [thumbnail, getIconUrl("presentation"), false]
  const HTML_THUMBNAILS = ["Markdown", "Code", "Text", "Document"]
  const IMAGE_THUMBNAILS = ["Image", "Video", "PDF", "Presentation"]
  const is_image = IMAGE_THUMBNAILS.includes(file_type)
  const iconURL = getIconUrl(file_type.toLowerCase())
  if (!is_image && !HTML_THUMBNAILS.includes(file_type))
    return [null, iconURL, true]
  return [
    `/api/method/drive.api.files.get_thumbnail?entity_name=${name}`,
    iconURL,
    is_image,
  ]
}