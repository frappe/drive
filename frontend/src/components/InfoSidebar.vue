<template>
  <div class="min-w-[400px] max-w-[400px] flex flex-col">
    <div v-if="$store.state.showInfo" class="mx-5 mb-3">
      <div class="my-4">
        <FeatherIcon
          name="x"
          class="h-4 cursor-pointer"
          @click="$store.commit('setShowInfo', false)"
        />
      </div>
      <div class="flex items-center">
        <img
          :src="
            getIconUrl(
              entity.is_group ? 'folder' : formatMimeType(entity.mime_type)
            )
          "
          class="h-5 mr-2.5"
        />
        <div class="font-semibold truncate text-2xl">
          {{ entity.title }}
        </div>
      </div>
    </div>
    <div
      class="flex cursor-pointer text-base"
      :class="$store.state.showInfo ? 'min-h-[45px]' : 'min-h-[48px]'"
    >
      <div
        class="w-1/2 flex border-b"
        :class="tab ? 'text-gray-600' : 'border-blue-500'"
        @click="tab = 0"
      >
        <div class="m-auto">Detail</div>
      </div>
      <div
        class="w-1/2 flex border-b"
        :class="tab ? 'border-blue-500' : 'text-gray-600'"
        @click="tab = 1"
      >
        <div class="m-auto">Comments</div>
      </div>
    </div>
    <div v-if="!tab" class="px-5 py-6 space-y-7 h-full flex flex-col z-0">
      <FileRender
        v-if="isImage && $store.state.showInfo"
        :previewEntity="entity"
      />
      <div v-if="entity.owner === 'me'">
        <div class="text-lg font-medium mb-4">Manage Access</div>
        <div class="flex flex-row">
          <Button @click="showShareDialog = true">Share</Button>
        </div>
      </div>
      <div class="grow">
        <div class="text-lg font-medium mb-4">Properties</div>
        <div class="flex text-base">
          <div class="w-1/2 text-gray-600 space-y-2">
            <div>Type</div>
            <div>Size</div>
            <div>Modified</div>
            <div>Created</div>
            <div>Owner</div>
          </div>
          <div class="w-1/2 space-y-2">
            <div>{{ formattedMimeType }}</div>
            <div>{{ entity.file_size }}</div>
            <div>{{ entity.modified }}</div>
            <div>{{ entity.creation }}</div>
            <div>{{ entity.owner }}</div>
          </div>
        </div>
      </div>
      <div class="text-gray-600 text-base">Viewers can download this file.</div>
    </div>
    <div v-else class="px-5 py-6 space-y-6 h-full overflow-y-auto">
      <div class="flex items-center gap-3">
        <Avatar :label="fullName" :imageURL="imageURL" class="h-7 w-7" />
        <input
          type="text"
          placeholder="Add comment or update..."
          @keydown.enter="postComment"
          v-model="comment"
          class="grow h-10 bg-white focus:bg-white border border-gray-200 focus:border-gray-200 rounded-lg text-[13px] placeholder-gray-600"
        />
      </div>
      <div v-for="comment in $resources.comments.data" class="flex gap-3">
        <Avatar :label="comment.comment_by" class="h-7 w-7" />
        <div>
          <span class="mb-1">
            <span class="text-[14px] font-medium">
              {{ comment.comment_by }}
            </span>
            <span class="text-gray-500 text-base">∙</span>
            <span class="text-gray-700 text-base">{{ comment.creation }}</span>
          </span>
          <div class="text-base">{{ comment.content }}</div>
        </div>
      </div>
    </div>
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entityName="entity.name"
    />
  </div>
</template>

<script>
import { FeatherIcon, Avatar, Input, call } from 'frappe-ui';
import ShareDialog from '@/components/ShareDialog.vue';
import { formatMimeType, formatDate } from '@/utils/format';
import FileRender from '@/components/FileRender.vue';
import getIconUrl from '@/utils/getIconUrl';

export default {
  name: 'InfoSidebar',
  components: {
    FeatherIcon,
    Avatar,
    Input,
    ShareDialog,
    FileRender,
  },

  props: {
    entity: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      tab: 0,
      comment: '',
      showShareDialog: false,
    };
  },

  methods: {
    async postComment() {
      try {
        await call('frappe.desk.form.utils.add_comment', {
          reference_doctype: 'Drive Entity',
          reference_name: this.entity.name,
          content: this.comment,
          comment_email: this.userId,
          comment_by: this.fullName,
        });
        this.comment = '';
        this.$resources.comments.fetch();
      } catch (e) {
        console.log(e);
      }
    },
  },

  computed: {
    userId() {
      return this.$store.state.auth.user_id;
    },
    fullName() {
      return this.$store.state.user.fullName;
    },
    imageURL() {
      return this.$store.state.user.imageURL;
    },
    isImage() {
      return this.entity.mime_type?.startsWith('image/');
    },
    formattedMimeType() {
      if (this.entity.is_group) return 'Folder';
      const file = formatMimeType(this.entity.mime_type);
      return file.charAt(0).toUpperCase() + file.slice(1);
    },
  },

  setup() {
    return { formatMimeType, getIconUrl };
  },

  resources: {
    comments() {
      return {
        method: 'drive.api.files.list_entity_comments',
        params: { entity_name: this.entity.name },
        onSuccess(data) {
          data.forEach((comment) => {
            comment.creation = formatDate(comment.creation);
          });
        },
        onError(error) {
          console.log(error);
        },
        auto: true,
      };
    },
  },
};
</script>
