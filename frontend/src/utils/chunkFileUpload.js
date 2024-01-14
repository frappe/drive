import { v4 as uuidv4 } from "uuid";

/* Simple function to chunk upload a file instead of dropzone JS 
   Currently only used in documents
*/

export async function uploadDriveEntity(file) {
  const fileUuid = uuidv4();
  const fileSize = file.size;
  const chunkSize = 5 * 1024 * 1024; // size of each chunk (5MB)

  let chunkByteOffset = 0;
  let chunkIndex = 0;
  const totalChunks = Math.ceil(file.size / chunkSize);
  while (chunkByteOffset < file.size) {
    let CurrentChunk = file.slice(chunkByteOffset, chunkByteOffset + chunkSize);
    const response = await uploadChunk(
      CurrentChunk,
      fileUuid,
      fileSize,
      chunkIndex,
      chunkSize,
      totalChunks,
      chunkByteOffset,
      file.name
    );

    if (chunkIndex === totalChunks - 1) {
      // This is the last chunk, handle the response here
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      const data = await response.json();
      return `/api/method/drive.api.files.get_file_content?entity_name=${data.message}`;
    }

    chunkByteOffset += chunkSize;
    chunkIndex++;
  }
}

async function uploadChunk(
  CurrentChunk,
  fileUuid,
  fileSize,
  chunkIndex,
  chunkSize,
  totalChunks,
  chunkByteOffset
) {
  const formData = new FormData();
  formData.append("total_file_size", fileSize);
  formData.append("total_chunk_count", totalChunks);
  formData.append("chunk_byte_offset", chunkByteOffset);
  formData.append("chunk_index", chunkIndex);
  formData.append("chunk_size", chunkSize);
  formData.append("file", CurrentChunk);
  formData.append("parent", "c41d55bac8ab40ca89ef2fd822616e88");
  formData.append("uuid", fileUuid);
  const response = await fetch("/api/method/drive.api.files.upload_file", {
    method: "POST",
    body: formData,
    headers: {
      "X-Frappe-CSRF-Token": window.csrf_token,
      Accept: "application/json",
    },
  });
  return response;
}
