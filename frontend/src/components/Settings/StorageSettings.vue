<template>
  <div class="flex mb-8 w-full flex-col items-start rounded-lg text-center">
    <h1 class="font-semibold mb-8">Storage</h1>
    <div class="flex flex-col items-start justify-start w-full mb-4">
      <span class="text-lg font-semibold text-gray-800 mb-3"
        >You have used {{ formatSize(usedSpace) }} out of
        {{ formatSize(planSizeLimit) }}</span
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
      class="flex flex-col items-start justify-start w-full rounded full px-1.5"
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
import { formatSize } from "../../utils/format"

export default {
  name: "StorageSettings",
  data() {
    return {
      fullName: this.$store.state.user.fullName,
      planSizeLimit: 50000000000,
      usedSpace: 0,
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
        url: "frappe.client.get",
        method: "GET",
        params: {
          doctype: "Drive Instance Settings",
        },
        onSuccess(data) {
          this.planSizeLimit = data.storage_limit
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n")
          } else {
            this.errorMessage = error.message
          }
        },
        auto: true,
      }
    },
    getDataByMimeType() {
      return {
        url: "drive.api.files.total_storage_used_by_file_kind",
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
        auto: true,
      }
    },
  },
  methods: {
    formatSize,
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
