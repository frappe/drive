<template>
  <div class="h-full w-full p-4">
    <div class="h-full grid place-items-center">
      <FileRender
        v-if="$resources.file.data"
        :preview-entity="$resources.file.data" />
    </div>
  </div>
</template>

<script>
import FileRender from "@/components/FileRender.vue";
import { formatSize, formatDate } from "@/utils/format";

export default {
  name: "File",
  components: {
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
      entity: null,
      dropdownItems: [
        {
          label: "Log out",
          onClick: () => this.$store.dispatch("logout"),
        },
      ],
      actionItems: [
        {
          label: "Download",
          onClick: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.entityName}&trigger_download=1`;
          },
        },
      ],
    };
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id;
    },
  },
  methods: {
    download() {
      window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.entityName}&trigger_download=1`;
    },
  },
  mounted() {
    this.$resources.file.fetch().then(() => {
      let currentBreadcrumbs = [];
      currentBreadcrumbs = this.$store.state.currentBreadcrumbs;
      if (
        !currentBreadcrumbs[currentBreadcrumbs.length - 1].route.includes(
          "/file"
        )
      ) {
        currentBreadcrumbs.push({
          label: this.entity.title,
          route: `/file/${this.entityName}`,
        });
        this.breadcrumbs = currentBreadcrumbs;
        this.$store.commit("setCurrentBreadcrumbs", currentBreadcrumbs);
      }
    });
  },

  resources: {
    file() {
      return {
        url: "drive.api.permissions.get_file_with_permissions",
        params: { entity_name: this.entityName },
        onSuccess(data) {
          this.entity = data;
          data.size_in_bytes = data.file_size;
          data.file_size = data.is_group ? "-" : formatSize(data.file_size);
          data.modified = formatDate(data.modified);
          data.creation = formatDate(data.creation);
          data.owner = data.owner === this.userId ? "me" : data.owner;
        },
        onError(error) {
          if (error?.messages.some((x) => x.startsWith("PermissionError")))
            window.location.href = "/";
        },
        auto: false,
      };
    },
  },
};
</script>
