<template>
  <Dialog
    v-model="show"
    :options="{
      title: '',
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="p-4">
        <!-- Header with icon and title -->
        <div class="flex items-center mb-4">
          <div class="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
            <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L5.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900">
            {{ entityName || 'Document' }}
          </h3>
        </div>

        <!-- Content -->
        <div class="mb-4">
          <div 
            class="text-gray-700 mb-3 leading-relaxed mentions-styled"
            v-html="formattedCommentContent"
          ></div>
        </div>

        <!-- Checkbox -->
        <div class="flex items-center mb-4">
          <input 
            id="grant-permission" 
            type="checkbox" 
            v-model="grantPermission"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          >
          <label for="grant-permission" class="ml-2 text-sm text-gray-700">
            Grant users view permission
          </label>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end space-x-2 px-4 pb-4">
        <Button
          variant="ghost"
          @click="handleCancel"
          class="px-4 py-2"
        >
          Cancel
        </Button>
        <Button
          variant="solid"
          @click="handlePost"
          :loading="isGranting"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700"
        >
          Post
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { Dialog, Button, Avatar } from "frappe-ui"

export default {
  name: "PermissionConfirmDialog",
  components: {
    Dialog,
    Button,
    Avatar,
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    usersWithoutPermission: {
      type: Array,
      default: () => [],
    },
    entityName: {
      type: String,
      required: true,
    },
    commentContent: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue", "grant-access", "post-without-permission", "cancel"],
  data() {
    return {
      isGranting: false,
      grantPermission: true, // Default checked
    }
  },
  computed: {
    show: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
      },
    },
    formattedCommentContent() {
      // If we have HTML content, return it as is (mentions are already styled)
      if (this.commentContent && this.commentContent.includes('<span data-type="mention"')) {
        return this.commentContent
      }
      
      // Fallback: just display the plain text
      return this.commentContent || 'Comment content will be displayed here...'
    },
  },
  methods: {
    handleCancel() {
      this.show = false
      this.$emit("cancel")
    },
    async handlePost() {
      this.isGranting = true
      try {
        if (this.grantPermission) {
          // Grant access and post
          await this.$emit("grant-access", this.usersWithoutPermission)
        } else {
          // Post without granting permission
          await this.$emit("post-without-permission")
        }
        this.show = false
      } catch (error) {
        console.error("Error posting comment:", error)
      } finally {
        this.isGranting = false
      }
    },
  },
}
</script>

<style scoped>
.mentions-styled :deep(span[data-type="mention"]) {
  background-color: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border-radius: 4px;
  padding: 2px 4px;
  font-weight: 500;
}
</style>
