export function getIconUrl(file_type) {
  return `/assets/drive/images/icons/${file_type?.toLowerCase() || 'unknown'}.svg`
}

export function getThumbnailUrl({ name, file_type, thumbnail, external }, view = 'list') {
  const iconURL = getIconUrl(file_type?.toLowerCase() ?? 'presentation')
  const showThumbnail = view !== 'list'

  if (external) return [showThumbnail ? thumbnail : null, iconURL, !showThumbnail]

  const HTML_THUMBNAILS = ['Markdown', 'Code', 'Text', 'Document']
  const IMAGE_THUMBNAILS = showThumbnail
    ? ['Image', 'Video', 'PDF', 'Presentation']
    : ['Image', 'Video', 'PDF']
  const is_image = IMAGE_THUMBNAILS.includes(file_type)

  if (!is_image && !HTML_THUMBNAILS.includes(file_type)) return [null, iconURL, true]
  return [`/api/method/drive.api.files.get_thumbnail?entity_name=${name}`, iconURL, is_image]
}
