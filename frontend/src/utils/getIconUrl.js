export function getIconUrl(file_type) {
  return new URL(
    `/src/assets/images/icons/${file_type.toLowerCase()}.svg`,
    import.meta.url
  )
}

export async function getThumbnailUrl(name, file_type) {
  const fileContent = await get_thumbnail_content(name)
  try {
    if (fileContent.type == "image/jpeg")
      return URL.createObjectURL(fileContent)

    const text = JSON.parse(await fileContent.text())
    if (!text.message) return getIconUrl(file_type.toLowerCase())
    return text.message.content
  } catch {
    return getIconUrl(file_type.toLowerCase())
  }
}

async function get_thumbnail_content(entity_name) {
  const fileUrl = `/api/method/drive.api.files.get_thumbnail?entity_name=${entity_name}`

  const content = await fetch(fileUrl)
  if (content.ok) {
    return content.blob()
  } else {
    throw new Error(`Request failed with status ${content.status}`)
  }
}
