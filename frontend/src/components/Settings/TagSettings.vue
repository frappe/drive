<template>
  <div class="flex items-center mb-6">
    <h1 class="font-semibold">Tags</h1>
    <Button
      variant="subtle"
      icon-left="plus"
      class="ml-auto"
      @click="showNewTagDialog = true"
    >
      New
    </Button>
  </div>
  <div v-for="(tag, i) in $resources.getTagsWithOwner.data" :key="tag.name">
    <div
      class="flex items-center justify-start text-sm py-1.5 gap-x-2 w-full"
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
      <Dropdown
        class="ml-auto"
        placement="right"
        :options="[
          {
            label: 'Edit',
            icon: 'edit-2',
            onClick: () => {
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
        <Button variant="ghost" @click="selectedTag = tag">
          <template #icon>
            <FeatherIcon
              name="more-horizontal"
              class="h-4 w-4"
            /> </template></Button
      ></Dropdown>
    </div>
  </div>
  <NewTagDialog
    v-if="showNewTagDialog"
    v-model="showNewTagDialog"
    @success="$resources.getTagsWithOwner.fetch()"
  ></NewTagDialog>
  <EditTagDialog
    v-if="showEditDialog"
    :tag="selectedTag"
    v-model="showEditDialog"
    @success="$resources.getTagsWithOwner.fetch()"
  ></EditTagDialog>
</template>
<script>
import { Dropdown, Button, FeatherIcon } from "frappe-ui"
import NewTagDialog from "./NewTagDialog.vue"
import EditTagDialog from "./EditTagDialog.vue"

export default {
  name: "TagSettings",
  components: {
    Dropdown,
    Button,
    FeatherIcon,
    NewTagDialog,
    EditTagDialog,
  },
  data() {
    return {
      showNewTagDialog: false,
      showEditDialog: false,
      selectedTag: null,
    }
  },
  resources: {
    getTagsWithOwner() {
      return {
        url: "drive.api.tags.get_tags_with_owner",
        onError(error) {
          console.log(error)
        },
        auto: true,
      }
    },
  },
}
</script>
