<template>
  <div class="flex items-center mb-6">
    <h1 class="font-semibold text-ink-gray-9">
      {{ __("Thẻ") }}
    </h1>
    <Button
      class="ml-auto mr-4 !bg-[#0149C1] text-white hover:!opacity-90"
      variant="solid"
      icon-left="plus"
      @click="showNewTagDialog = true"
    >
      {{ __("Tạo mới") }}
    </Button>
  </div>
  <div class="flex flex-col items-stretch justify-start overflow-y-auto">
    <div
      v-for="(tag, i) in $resources.getTagsWithOwner.data"
      :key="tag.name"
    >
      <div
        class="flex items-center justify-start text-sm py-1.5 gap-x-1.5 w-full"
        :class="i > 0 ? 'border-t' : ''"
      >
        <svg
          class="h-2.5"
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
        <span class="text-sm text-ink-gray-8">{{ tag.title }}</span>
        <Dropdown
          class="ml-auto"
          placement="right"
          :options="[
            {
              label: 'Chỉnh sửa',
              icon: 'edit-2',
              onClick: () => {
                showEditDialog = true
              },
            },
            {
              label: 'Xóa',
              theme: 'red',
              icon: 'trash-2',
              onClick: () => {
                activeTag = tag
                showDeleteDialog = true
              },
            },
          ]"
        >
          <Button
            variant="ghost"
            @click="selectedTag = tag"
          >
            <template #icon>
              <LucideMoreHorizontal class="size-4" />
            </template>
          </Button>
        </Dropdown>
      </div>
    </div>
    <div
      v-if="!$resources.getTagsWithOwner.data?.length"
      class="h-full w-full flex flex-col items-center justify-center my-auto"
    >
      <LucideTag class="h-7 stroke-1 text-ink-gray-5" />
      <span class="text-ink-gray-8 text-sm mt-2">Không có thẻ nào</span>
    </div>
  </div>
  <NewTagDialog
    v-if="showNewTagDialog"
    v-model="showNewTagDialog"
    @success="$resources.getTagsWithOwner.fetch()"
  />
  <EditTagDialog
    v-if="showEditDialog"
    v-model="showEditDialog"
    :tag="selectedTag"
    @success="$resources.getTagsWithOwner.fetch()"
  />
  <Dialog
    v-if="showDeleteDialog"
    v-model="showDeleteDialog"
    :options="{
      title: 'Xóa thẻ',
      message: `Bạn có chắc chắn muốn xóa thẻ ${selectedTag.title}? Hành động này không thể hoàn tác`,
      size: 'sm',
      actions: [
        {
          label: 'Xác nhận',
          variant: 'subtle',
          theme: 'red',
          onClick: () => {
            $resources.deleteTag.submit(), (showDeleteDialog = false)
          },
        },
      ],
    }"
  />
</template>
<script>
import { Button, Dialog, Dropdown } from "frappe-ui"
import EditTagDialog from "./EditTagDialog.vue"
import NewTagDialog from "./NewTagDialog.vue"

export default {
  name: "TagSettings",
  components: {
    Dropdown,
    Button,
    NewTagDialog,
    EditTagDialog,
    Dialog,
  },
  data() {
    return {
      showNewTagDialog: false,
      showEditDialog: false,
      showDeleteDialog: false,
      selectedTag: null,
    }
  },
  computed: {
    deleteMessage() {
      return `Bạn có chắc chắn muốn xóa thẻ "blog"? Hành động này không thể hoàn tác. Tất cả các tệp có thẻ này cũng sẽ bị mất thẻ.`
    },
  },
  resources: {
    deleteTag() {
      return {
        url: "drive.api.tags.delete_tag",
        params: {
          tag: this.selectedTag?.name,
        },
        onSuccess() {
          this.$resources.getTagsWithOwner.fetch()
        },
        onError(error) {
          console.log(error)
        },
        auto: false,
      }
    },
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
