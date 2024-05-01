import { v4 as uuidv4 } from "uuid"

/* Simple function to chunk upload a file instead of dropzone JS 
   Currently only used in documents
*/

export async function uploadDriveEntity(file, parent_entity_name) {
  const fileUuid = uuidv4()
  const chunkSize = 5 * 1024 * 1024 // size of each chunk (5MB)
  let chunkByteOffset = 0
  let chunkIndex = 0
  const totalChunks = Math.ceil(file.size / chunkSize)
  while (chunkByteOffset < file.size) {
    let CurrentChunk = file.slice(chunkByteOffset, chunkByteOffset + chunkSize)
    const response = await uploadChunk(
      file.name,
      CurrentChunk,
      fileUuid,
      file.size,
      file.type,
      chunkIndex,
      chunkSize,
      totalChunks,
      chunkByteOffset,
      parent_entity_name
    )

    if (chunkIndex === totalChunks - 1) {
      // This is the last chunk, handle the response here
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }
      const data = await response.json()
      return `/api/method/drive.api.embed.get_file_content?embed_name=${data.message}&parent_entity_name=${parent_entity_name}`
    }

    chunkByteOffset += chunkSize
    chunkIndex++
  }
}

async function uploadChunk(
  fileName,
  CurrentChunk,
  fileUuid,
  fileSize,
  fileType,
  chunkIndex,
  chunkSize,
  totalChunks,
  chunkByteOffset,
  parent_entity_name
) {
  const formData = new FormData()
  formData.append("file_name", fileName)
  formData.append("total_file_size", fileSize)
  formData.append("mime_type", fileType)
  formData.append("total_chunk_count", totalChunks)
  formData.append("chunk_byte_offset", chunkByteOffset)
  formData.append("chunk_index", chunkIndex)
  formData.append("chunk_size", chunkSize)
  formData.append("file", CurrentChunk)
  formData.append("parent", parent_entity_name)
  formData.append("uuid", fileUuid)
  const response = await fetch(
    window.location.origin + "/api/method/drive.api.embed.upload_chunked_file",
    {
      method: "POST",
      body: formData,
      headers: {
        "X-Frappe-CSRF-Token": window.csrf_token,
        Accept: "application/json",
      },
    }
  )
  return response
}
