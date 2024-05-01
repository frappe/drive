<template>
  <transition
    enter-active-class="duration-150 ease-out"
    enter-from-class="transform opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="transform opacity-0"
  >
    <div
      v-if="selectedEntities.length"
      class="absolute inset-x-0 bottom-6 mx-auto w-max text-base"
    >
      <div
        class="flex min-w-[596px] items-center space-x-3 rounded-lg bg-white px-4 py-2 shadow-2xl"
      >
        <div
          class="flex flex-1 justify-between border-r border-gray-300 text-gray-900"
        >
          <div class="flex items-center space-x-3">
            <Checkbox
              :model-value="true"
              :disabled="true"
              class="text-gray-900"
            />
            <div>{{ selectedEntities.length }} selected</div>
          </div>
          <div>
            <Button
              v-if="IsDownloadEnabled()"
              icon-left="download"
              class="flex items-center text-gray-700"
              variant="ghost"
              @click="Download()"
            >
              Download
            </Button>
            <Button
              v-if="selectedEntities.length < 2"
              icon-left="link-2"
              class="flex items-center text-gray-700"
              variant="ghost"
            >
              Get Link
            </Button>
            <Button
              icon-left="star"
              class="flex items-center text-gray-700"
              variant="ghost"
            >
              Favourite
            </Button>
          </div>
        </div>
        <Button
          icon-left="trash-2"
          class="flex items-center text-red-500"
          variant="ghost"
        >
          Delete
        </Button>
        <Button icon="x" variant="ghost" />
      </div>
    </div>
  </transition>
</template>

<script setup>
import { useStore } from "vuex"
import { Checkbox, Button } from "frappe-ui"
import { computed } from "vue"
import {
  folderDownload,
  selectedEntitiesDownload,
} from "@/utils/folderDownload"

defineOptions({
  inheritAttrs: false,
})

const store = useStore()
let selectedEntities = computed(() => {
  return store.state.entityInfo
})

function Download() {
  if (selectedEntities.value.length === 1) {
    window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${selectedEntities.value[0].name}&trigger_download=1`
  }
  if (selectedEntities.value.length > 1) {
    selectedEntitiesDownload(selectedEntities.value)
  } else if (selectedEntities.value[0].is_group === 1) {
    folderDownload(selectedEntities.value[0])
  }
}

function IsDownloadEnabled() {
  if (selectedEntities.value[0].document) {
    return false
  }
  const allEntitiesSatisfyCondition = selectedEntities.value.every((entity) => {
    return entity.allow_download || entity.write || entity.owner === "You"
  })
  return allEntitiesSatisfyCondition
}

/* function IsFavouriteEnabled(){
  if (selectedEntities.value.length > 0 &&
  this.selectedEntities.every((x) => !x.is_favourite))
} */

/*   window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;

  let isEnabled;
  if (selectedEntities.value.length === 1 && !selectedEntities.value[0].is_group) {
    isEnabled = true;
  }
  return isEnabled; */
/* if (selectedEntities.value.length === 1) {
    if (
      selectedEntities.value.length === 1 
      && !selectedEntities.value[0].is_group
      ) {
        isEnabled = !selectedEntities.value[0].document
      }
  }
  if (selectedEntities.value.length) {
    const allEntitiesSatisfyCondition = selectedEntities.value.every(
      (entity) => {
        return (
          entity.allow_download ||
          entity.write ||
          entity.owner === "You"
        );
      }
    );
    return allEntitiesSatisfyCondition;
  } */
/* } */
/* 

<!-- // Download -->
<!-- onClick: () => 

  // Favourite

  {
    label: "Favourite",
    icon: "star",
    onClick: () => {
      this.$resources.toggleFavourite.submit();
    },
    isEnabled: () => {
      return (
        this.selectedEntities.length > 0 &&
        this.selectedEntities.every((x) => !x.is_favourite)
      );
    },
  },
  {
    label: "Unfavourite",
    icon: "star",
    onClick: () => {
      this.$resources.toggleFavourite.submit();
    },
    isEnabled: () => {
      return (
        this.selectedEntities.length > 0 &&
        this.selectedEntities.every((x) => x.is_favourite)
      );
    },
  }, */
</script>
