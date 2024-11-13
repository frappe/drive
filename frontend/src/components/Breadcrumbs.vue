<template>
  <div ref="container" class="flex justify-items-center items-center text-base">
    <template v-if="dropDownItems.length">
      <Dropdown class="h-7" :options="dropDownItems">
        <Button variant="ghost">
          <template #icon>
            <svg
              class="w-4 text-gray-600"
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="1" />
              <circle cx="19" cy="12" r="1" />
              <circle cx="5" cy="12" r="1" />
            </svg>
          </template>
        </Button>
      </Dropdown>
      <span class="ml-1 mr-0.5 text-base text-gray-500" aria-hidden="true">
        /
      </span>
    </template>

    <div class="flex">
      <router-link
        v-for="(item, index) in crumbs"
        :key="item.label"
        class="text-md line-clamp-1 sm:text-lg font-medium cursor-pointer"
        :class="[
          $store.state.currentBreadcrumbs.length === 1
            ? 'text-black'
            : ' hover:text-gray-800 text-gray-600',
        ]"
        :to="item.route"
      >
        <span> {{ __(item.label) }}</span>
        <span v-show="index < crumbs.length - 1" class="mx-1">/</span>
      </router-link>
    </div>

    <span
      v-if="$store.state.currentBreadcrumbs.length > 1"
      class="text-black text-md line-clamp-1 sm:text-lg font-medium cursor-pointer"
      @click="canShowRenameDialog"
    >
      <span class="ml-1">/</span>
      {{ currentTitle }}
    </span>
  </div>
  <RenameDialog
    v-if="showRenameDialog"
    v-model="showRenameDialog"
    :entity="entity"
    @success="
      (data) => {
        showRenameDialog = false
        currentTitle = data.title
      }
    "
  />
</template>
<script>
import RenameDialog from "@/components/RenameDialog.vue"
import { Dropdown } from "frappe-ui"

export default {
  name: "Breadcrumbs",
  components: { RenameDialog, Dropdown },
  data() {
    return {
      title: "",
      showRenameDialog: false,
    }
  },
  computed: {
    entity() {
      if (this.$route.name === "Folder") {
        this.$store.commit("setEntityInfo", this.$store.state.currentFolder)
      }
      return this.$store.state.entityInfo[0]
    },
    breadcrumbLinks() {
      let arr = this.$store.state.currentBreadcrumbs
      if (arr.length > 1) {
        return arr.slice(0, -1)
      }
      return arr
    },
    currentTitle: {
      get() {
        const { breadcrumbLinks, $route, $store } = this
        const { name } = $route
        const lastBreadcrumb = breadcrumbLinks[breadcrumbLinks.length - 1]
        const storeTitle = $store.state.entityInfo[0]?.title
        const folderTitle = $store.state.currentFolder[0]?.title
        let result

        switch (name) {
          case "Folder":
            result = folderTitle
            break
          case "Document":
          case "File":
            result =
              lastBreadcrumb.label !== storeTitle
                ? storeTitle
                : lastBreadcrumb.label
            break
          default:
            result = lastBreadcrumb.label
        }
        document.title = result
        return result
      },
      set(newValue) {
        return newValue
      },
    },
    currentRoute() {
      return this.breadcrumbLinks[this.breadcrumbLinks.length - 1].route
    },
    currentEntityName() {
      return this.currentRoute.split("/")[2]
    },
    dropDownItems() {
      if (window.innerWidth > 640) return []
      let allExceptLastTwo = this.breadcrumbLinks.slice(0, -1)
      return allExceptLastTwo.map((item) => {
        let onClick = item.onClick
          ? item.onClick
          : () => this.$router.push(item.route)
        return {
          ...item,
          icon: null,
          label: item.label,
          onClick,
        }
      })
    },
    crumbs() {
      if (window.innerWidth > 640) return this.breadcrumbLinks
      return this.breadcrumbLinks.slice(-1)
    },
  },
  methods: {
    isLastItem(index) {
      return this.breadcrumbLinks.length > 1
        ? index === this.breadcrumbLinks.length - 1
        : false
    },
    canShowRenameDialog() {
      if (this.$route.name === "Folder") {
        if (
          (this.$store.state.currentFolder[0]?.owner === "You") |
          this.$store.state.currentFolder[0]?.write
        ) {
          return (this.showRenameDialog = true)
        }
      } else if (
        (this.$store.state.entityInfo[0]?.owner === "You") |
        (this.$store.state.entityInfo[0]?.write === 1)
      ) {
        return (this.showRenameDialog = true)
      }
    },
  },
}
</script>
