<template>
  <h1 class="font-semibold mb-4">Storage</h1>
  <UserStorage
    v-if="showFileStorage"
    :used-space="fileUsedSpace"
    :plan-size-limit="filePlanSizeLimit"
    :data="$resources.getOwnedFiles.data"
  >
    <template #control>
      <div
        v-if="storageQuotaEnabled"
        class="bg-gray-100 rounded-[10px] space-x-0.5 h-7 w-28 flex items-center px-0.5 py-1"
      >
        <Button
          variant="ghost"
          class="max-h-6 leading-none transition-colors focus:outline-none"
          :class="[
            showFileStorage === false
              ? 'bg-white shadow-sm hover:bg-white active:bg-white'
              : '',
          ]"
          @click="showFileStorage = false"
        >
          System
        </Button>
        <Button
          variant="ghost"
          class="max-h-6 leading-none transition-colors focus:outline-none"
          :class="[
            showFileStorage === true
              ? 'bg-white shadow-sm hover:bg-white active:bg-white'
              : '',
          ]"
          @click="showFileStorage = true"
        >
          You
        </Button>
      </div>
    </template>
  </UserStorage>
  <SystemStorage
    v-else
    :used-space="systemUsedSpace"
    :plan-size-limit="systemPlanSizeLimit"
    :entities="$resources.getDataByMimeType.data"
  >
    <template #control>
      <div
        v-if="storageQuotaEnabled"
        class="bg-gray-100 rounded-[10px] space-x-0.5 h-7 w-28 flex items-center px-0.5 py-1"
      >
        <Button
          variant="ghost"
          class="max-h-6 leading-none transition-colors focus:outline-none"
          :class="[
            showFileStorage === false
              ? 'bg-white shadow-sm hover:bg-white active:bg-white'
              : '',
          ]"
          @click="showFileStorage = false"
        >
          System
        </Button>
        <Button
          variant="ghost"
          class="max-h-6 leading-none transition-colors focus:outline-none"
          :class="[
            showFileStorage === true
              ? 'bg-white shadow-sm hover:bg-white active:bg-white'
              : '',
          ]"
          @click="showFileStorage = true"
        >
          You
        </Button>
      </div>
    </template>
  </SystemStorage>
</template>
<script>
import { formatSize, base2BlockSize, formatMimeType } from "../../utils/format"
import { getIconUrl } from "../../utils/getIconUrl"
import SystemStorage from "./SystemStorage.vue"
import UserStorage from "./UserStorage.vue"

export default {
  name: "StorageSettings",
  components: {
    SystemStorage,
    UserStorage,
  },
  data() {
    return {
      fullName: this.$store.state.user.fullName,
      showFileStorage: false,
      systemPlanSizeLimit: 50000000000,
      filePlanSizeLimit: 50000000000,
      fileUsedSpace: 0,
      systemUsedSpace: 0,
      storageQuotaEnabled: false,
      fileKindColorMap: {
        Archive: "#C2A88D",
        Application: "#f472b6",
        Image: "#34BAE3",
        Video: "#E86C13",
        Audio: "#9C45E3",
        Document: "#0073CA",
        Spreadsheet: "#30A66D",
        Presentation: "#F5BA14",
        Text: "#E2E2E2",
        PDF: "#E03636",
        Book: "#E2E2E2",
        Unknown: "#3f3f46",
      },
    }
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded
    },
    firstName() {
      return this.$store.state.user.fullName.split(" ")
    },
    isDriveadmin() {
      return this.$store.state.user.role === "Drive Admin"
    },
    /* fullName() {
        return this.$store.state.user.fullName;
      }, */
    imageURL() {
      return this.$store.state.user.imageURL
    },
  },
  resources: {
    storageLimit() {
      return {
        url: "drive.api.storage.get_max_storage",
        method: "GET",
        auto: true,
        onSuccess(data) {
          if (data.quota) {
            this.storageQuotaEnabled = true
            this.$resources.getOwnedFiles.fetch()
          }
          this.$resources.getDataByMimeType.fetch()
          this.filePlanSizeLimit = data.quota
          this.systemPlanSizeLimit = data.limit
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
        url: "drive.api.storage.total_storage_used_by_file_kind",
        onError(error) {
          console.log(error)
        },
        onSuccess(data) {
          data.forEach((item) => {
            item.color = this.fileKindColorMap[item.file_kind]
            item.percentageRaw =
              (100 * item.total_size) / this.systemPlanSizeLimit
            item.percentageFormat = this.formatPercent(item.percentageRaw)
            item.h_size = formatSize(item.total_size)
            this.systemUsedSpace = this.systemUsedSpace + item.total_size
          })
          data.sort((a, b) => b.total_size - a.total_size)
        },
        auto: false,
      }
    },
    getOwnedFiles() {
      return {
        url: "drive.api.storage.get_owned_files_by_storage",
        onError(error) {
          console.log(error)
        },
        onSuccess(data) {
          data.total.forEach((item) => {
            item.color = this.fileKindColorMap[item.file_kind]
            item.percentageRaw = (100 * item.file_size) / this.filePlanSizeLimit
            item.percentageFormat = this.formatPercent(item.percentageRaw)
            item.h_size = formatSize(item.file_size)
            this.fileUsedSpace = this.fileUsedSpace + item.file_size
          })
          this.showFileStorage = true
        },
        auto: false,
      }
    },
  },
  methods: {
    formatMimeType,
    getIconUrl,
    formatSize,
    base2BlockSize,
    formatPercent(num) {
      return new Intl.NumberFormat("default", {
        style: "percent",
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      }).format(num / 100)
    },
  },
}
</script>
