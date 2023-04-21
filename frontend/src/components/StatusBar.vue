<template>
  <div class="fixed bottom-0 w-full bg-white p-4">

    <hr class="border-t border-gray-400 mb-4">

    <div class="flex flex-col xl:flex-row justify-between items-center">
      <div class="text-sm flex items-center space-x-2">
        <img src="../assets/images/icons/image.svg" alt="photo icon" class="h-5 w-5">
        <p class="font-medium mr-4">{{ countPhotos() }} <span id="num-photos"></span></p>
        <img src="../assets/images/icons/video.svg" alt="video icon" class="h-5 w-5">
        <p class="font-medium mr-4">{{ countVideos() }} <span id="num-videos"></span></p>
        <img src="../assets/images/icons/folder.svg" alt="folder icon" class="h-5 w-5">
        <p class="font-medium mr-4">{{ countFolders() }} <span id="num-folders"></span></p>
        <img src="../assets/images/icons/files.svg" alt="folder icon" class="h-5 w-5">
        <p class="font-medium">{{ countFiles() }}<span id="num-files"></span></p>
        <img src="../assets/images/icons/storage.svg" class="h-5 w-5 mr-2">
        <p class="font-medium">{{ totalSize() }} <span id="total-size"></span></p>
      </div>
    </div>

  </div>
</template>


<script>

export default {
  props: {
    folderContents: {
      type: Array,
      required: true,
    },
  },
  methods: {
    countPhotos() {
      let numPhotos = 0;
      this.folderContents.forEach((entity) => {
        if (entity.mime_type == "image/jpeg" || entity.mime_type == "image/png") {
          numPhotos++;
        }
      });
      return numPhotos;
      },

    countVideos() {
      let numVideos = 0;
      this.folderContents.forEach((entity) => {
        if (entity.mime_type == "video/mp4") {
          numVideos++;
        }
      });
      return numVideos;
    },

    countFolders() {
      let numFolders = 0;
      this.folderContents.forEach((entity) => {
        if (entity.is_group) {
          numFolders++;
        }
      });
      return numFolders;
    },

    countFiles() {
      let numFiles = 0;
      this.folderContents.forEach((entity) => {
        if (!entity.is_group && entity.mime_type == "application/msword" ) {
          numFiles++;
        }
      });
      return numFiles;
    }, 
    totalSize() {
      let total = 0;
      this.folderContents.forEach((entity) => {
        if (entity.is_group === "1") {
          total += this.getFolderSize(entity);
        } else {
          total += parseInt(entity.size_in_bytes);
        }
      });
      const units = ["B", "KB", "MB", "GB"];
      let unitIndex = 0;
      while (total >= 1024 && unitIndex < units.length - 1) {
        total /= 1024;
        unitIndex++;
      }
      return `${total.toFixed(2)} ${units[unitIndex]}`;
    },
    getFolderSize(folder) {
      let size = 0;
      folder.children.forEach((entity) => {
        if (entity.is_group === "1") {
          size += this.getFolderSize(entity);
        } else {
          // file
          size += parseInt(entity.size_in_bytes);
        }
      });
      return size;
    },
  },
};
</script>

