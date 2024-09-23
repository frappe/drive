<template>
  <div class="flex items-center mb-6">
    <h1 class="font-semibold">Tags</h1>
    <Button
      variant="subtle"
      icon-left="plus"
      class="ml-auto"
      @click="NewTagDialog = !NewTagDialog"
    >
      New
    </Button>
  </div>
  <div v-for="(tag, i) in $resources.getDataByMimeType.data" :key="tag.name">
    <div
      class="flex items-center justify-start text-base py-2.5 gap-x-2 w-full"
      :class="i > 0 ? 'border-t' : ''"
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle
          r="4.5"
          cx="8"
          cy="8"
          :fill="tag.color"
          :stroke="tag.color"
          stroke-width="3"
        />
      </svg>
      <span class="text-base">{{ tag.title }}</span>
      <!-- <span class="ml-auto">{{ tag.owner }}</span> -->
      <Dropdown
        class="ml-auto"
        placement="right"
        :options="[
          {
            label: 'Edit',
            icon: 'edit-2',
            onClick: () => {
              activeTag = tag
              showEditDialog = true
            },
          },
          {
            label: 'Delete',
            icon: 'trash-2',
            onClick: () => {
              activeTag = tag
              showDeleteDialog = true
            },
          },
        ]"
      >
        <Button variant="ghost">
          <template #icon>
            <FeatherIcon
              name="more-horizontal"
              class="h-4 w-4"
            /> </template></Button
      ></Dropdown>
    </div>
  </div>
  <Dialog v-model="NewTagDialog"></Dialog>
</template>
<script>
import { Dropdown, Button, FeatherIcon, Dialog } from "frappe-ui"
export default {
  name: "TagSettings",
  components: {
    Dropdown,
    Button,
    FeatherIcon,
    Dialog,
  },
  data() {
    return {
      NewTagDialog: false,
      SelectedTag: null,
    }
  },
  resources: {
    storageLimit() {
      return {
        url: "drive.api.storage.get_max_storage",
        method: "GET",
        auto: true,
        onSuccess(data) {
          this.planSizeLimit = data
          this.$resources.getDataByMimeType.fetch()
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n")
          } else {
            this.errorMessage = error.message
          }
        },
      }
    },
    getDataByMimeType() {
      return {
        url: "drive.api.tags.get_tags_with_owner",
        onError(error) {
          console.log(error)
        },
        onSuccess(data) {
          console.log(data)
        },
        auto: false,
      }
    },
  },
}
</script>
