export function getIconUrl(mime_type) {
  return new URL(`/src/assets/images/icons/${mime_type}.svg`, import.meta.url)
}

export async function getThumbnailUrl(mime_type, name) {
  try {
    const fileContent = await get_thumbnail_content(name)
    return fileContent.type == "image/jpeg"
      ? URL.createObjectURL(fileContent)
      : getIconUrl(mime_type)
  } catch {
    return getIconUrl(mime_type)
  }
}

async function get_thumbnail_content(entity_name) {
  const fileUrl = `/api/method/drive.api.files.get_thumbnail?entity_name=${entity_name}`

  const content = await fetch(fileUrl)
  if (content.ok) {
    return content.blob()
  } else {
    throw new Error(`Request failed with status ${response.status}`)
  }
}
