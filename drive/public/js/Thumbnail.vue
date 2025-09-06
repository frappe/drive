<template>
  <img v-if="!imgLoaded" loading="lazy" :src="backupLink" :draggable="false" />
  <img
    v-show="imgLoaded"
    :src="src"
    :draggable="false"
    @error="src = backupLink"
    @load="imgLoaded = true"
  />
</template>
<script setup>
import { ref } from "vue";
const props = defineProps({
  node: Object,
});

// Copied from utils
function getThumbnailUrl(name, file_type) {
  const HTML_THUMBNAILS = ["Markdown", "Code", "Text", "Document"];
  const IMAGE_THUMBNAILS = ["Image", "Video", "PDF", "Presentation"];
  const is_image = IMAGE_THUMBNAILS.includes(file_type);
  if (!file_type) console.log(props.node);
  const iconURL = `/src/assets/images/icons/${file_type.toLowerCase()}.svg`;
  if (!is_image && !HTML_THUMBNAILS.includes(file_type))
    return [null, iconURL, true];
  return [
    `/api/method/drive.api.files.get_thumbnail?entity_name=${name}`,
    iconURL,
    is_image,
  ];
}

const [thumbnailLink, backupLink, is_image] = getThumbnailUrl(
  props.node.value,
  props.node.file_type
);
const src = ref(thumbnailLink || backupLink);
const imgLoaded = ref(false);
</script>
<style>
img {
  border-radius: 0.25rem;
  object-fit: cover;
  width: 16px;
  height: 16px;
  align-self: center;
}
</style>
