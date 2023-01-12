<template>
  <div class="h-full flex">
    <div class="w-full">
      <div
        class="py-3 px-6 h-16 md:h-[48px] z-10 flex items-center justify-between border-b"
      >
        <p class="truncate text-lg text-gray-600">
          {{
            `${$resources.file.data?.modified} ∙ ${$resources.file.data?.file_size}`
          }}
        </p>
        <h3 class="truncate font-medium text-2xl">
          {{ $resources.file.data?.title }}
        </h3>
        <div class="flex items-center">
          <div class="z-20 space-x-4">
            <Button
              icon="download"
              appearance="minimal"
              @click="download"
            ></Button>
            <Dropdown :options="actionItems" placement="right">
              <button
                class="flex items-center max-w-xs text-sm text-white rounded-full focus:outline-none focus:shadow-solid"
                id="actions-menu"
                aria-label="Actions menu"
                aria-haspopup="true"
              >
                <div class="flex items-center gap-4">
                  <Button appearance="minimal" icon="more-horizontal"></Button>
                </div>
              </button>
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="p-6 grow grid place-items-center md:h-[calc(100%-48px)]">
        <FileRender
          v-if="$resources.file.data"
          :previewEntity="$resources.file.data"
          class="w-full"
        />
      </div>
    </div>
    <InfoSidebar
      v-if="$resources.file.data"
      class="border-l"
      :entity="$resources.file.data"
    />
  </div>
</template>

<script>
import { Avatar, Dropdown } from 'frappe-ui';
import InfoSidebar from '@/components/InfoSidebar.vue';
import FileRender from '@/components/FileRender.vue';
import { formatSize, formatDate } from '@/utils/format';

export default {
  name: 'File',
  components: {
    Avatar,
    Dropdown,
    InfoSidebar,
    FileRender,
  },
  props: {
    entityName: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      dropdownItems: [
        {
          label: 'Log out',
          handler: () => this.$store.dispatch('logout'),
        },
      ],
      actionItems: [
        {
          label: 'Download',
          handler: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.entityName}&trigger_download=1`;
          },
        },
      ],
    };
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id;
      m;
    },
  },
  methods: {
    download() {
      window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.entityName}&trigger_download=1`;
    },
  },
  resources: {
    file() {
      return {
        url: 'drive.api.permissions.get_file_with_permissions',
        params: { entity_name: this.entityName },
        onSuccess(data) {
          data.size_in_bytes = data.file_size;
          data.file_size = data.is_group ? '-' : formatSize(data.file_size);
          data.modified = formatDate(data.modified);
          data.creation = formatDate(data.creation);
          data.owner = data.owner === this.userId ? 'me' : data.owner;
        },
        onError(error) {
          if (error?.messages.some((x) => x.startsWith('PermissionError')))
            window.location.href = '/';
        },
        auto: true,
      };
    },
  },
};
</script>
