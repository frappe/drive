<template>
  <h1 class="font-semibold mb-8">Storage</h1>
  <div
    v-if="!usedSpace"
    class="h-full w-full flex flex-col items-center justify-center my-auto"
  >
    <Cloud class="h-7 stroke-1 text-gray-600" />
    <span class="text-gray-800 text-sm mt-2">No Storage Used</span>
  </div>
  <div v-if="storageQuotaEnabled && usedSpace">
    <div class="flex flex-col items-start justify-start w-full mb-4">
      <span class="text-lg font-semibold text-gray-800 mb-3"
        >You have used {{ formatSize(usedSpace) }} out of
        {{ base2BlockSize(planSizeLimit) }}</span
      >
      <div
        class="w-full flex justify-start items-start bg-gray-50 border rounded overflow-clip h-7 pl-0"
      >
        <div
          v-for="i in $resources.getOwnedFiles.data.total"
          :key="i.file_kind"
          class="h-7"
          :style="{
            backgroundColor: i.color,
            width: i.percentageFormat,
            paddingRight: `${5 + i.percentageRaw}px`,
          }"
        ></div>
      </div>
    </div>
    <div
      class="flex flex-col items-start justify-start w-full rounded full px-1.5 overflow-y-auto"
    >
      <div
        v-for="i in $resources.getOwnedFiles.data.entities"
        :key="i.name"
        class="w-full border-b flex items-center justify-start py-2.5 gap-x-2"
      >
        <img :src="getIconUrl(formatMimeType(i.mime_type))" />
        <span class="text-gray-800 text-base">{{ i.title }}</span>
        <span class="text-gray-800 text-base ml-auto">{{
          formatSize(i.file_size)
        }}</span>
      </div>
    </div>
  </div>
  <div v-else>
    <div class="flex flex-col items-start justify-start w-full mb-4">
      <span class="text-lg font-semibold text-gray-800 mb-3"
        >You have used {{ formatSize(usedSpace) }} out of
        {{ base2BlockSize(planSizeLimit) }}</span
      >
      <div
        class="w-full flex justify-start items-start bg-gray-50 border rounded overflow-clip h-7 pl-0"
      >
        <div
          v-for="i in $resources.getDataByMimeType.data"
          :key="i.file_kind"
          class="h-7"
          :style="{
            backgroundColor: i.color,
            width: i.percentageFormat,
            paddingRight: `${5 + i.percentageRaw}px`,
          }"
        ></div>
      </div>
    </div>
    <div
      class="flex flex-col items-start justify-start w-full rounded full px-1.5 overflow-y-auto"
    >
      <div
        v-for="i in $resources.getDataByMimeType.data"
        :key="i.file_kind"
        class="w-full border-b flex items-center justify-start py-4 gap-x-2"
      >
        <div
          class="h-2 w-2 rounded-full"
          :style="{
            backgroundColor: i.color,
          }"
        ></div>
        <span class="text-gray-800 text-base">{{ i.file_kind }}</span>
        <span class="text-gray-800 text-base ml-auto">{{ i.h_size }}</span>
      </div>
    </div>
  </div>
</template>
<script>
import { formatSize, base2BlockSize, formatMimeType } from "../../utils/format"
import Cloud from "@/components/EspressoIcons/Cloud.vue"
import { getIconUrl } from "../../utils/getIconUrl"

export default {
  name: "StorageSettings",
  components: {
    Cloud,
  },
  data() {
    return {
      fullName: this.$store.state.user.fullName,
      planSizeLimit: 50000000000,
      usedSpace: 0,
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
          } else {
            this.$resources.getDataByMimeType.fetch()
          }
          this.planSizeLimit = data.limit || data.quota
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
            item.percentageRaw = (100 * item.total_size) / this.planSizeLimit
            item.percentageFormat = this.formatPercent(item.percentageRaw)
            item.h_size = formatSize(item.total_size)
            this.usedSpace = this.usedSpace + item.total_size
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
            item.percentageRaw = (100 * item.file_size) / this.planSizeLimit
            item.percentageFormat = this.formatPercent(item.percentageRaw)
            item.h_size = formatSize(item.file_size)
            this.usedSpace = this.usedSpace + item.file_size
          })
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
