export function getIconUrl(mime_type) {
  return new URL(`/src/assets/images/icons/${mime_type}.svg`, import.meta.url);
}

export async function thumbnail_getIconUrl(mime_type, name) {
  if (mime_type === "image") {
    return get_file_content(name).then((fileContent) => {
      return URL.createObjectURL(fileContent);
    });
  } else {
    return Promise.resolve(
      new URL(`/src/assets/images/icons/${mime_type}.svg`, import.meta.url)
    );
  }
}

function get_file_content(entity_name) {
  const fileUrl =
    "/api/method/" +
    `drive.api.files.get_file_content?entity_name=${entity_name}`;

  return fetch(fileUrl).then((response) => {
    if (response.ok) {
      return response.blob();
    } else {
      throw new Error(`Request failed with status ${response.status}`);
    }
  });
}
