<template>
  <div
    ref="container"
    class="h-full w-full pt-3.5 px-4 pb-5 overflow-y-auto flex flex-col"
    @mousedown.prevent="(e) => dragSelectStart(e)"
    @contextmenu="handleContextMenu"
  >
    <DriveToolBar :column-headers="showSort ? columnHeaders : null" />

    <!-- This sucks, redo it -->
    <FolderContentsError v-if="getEntities.error" :error="getEntities.error" />
    <NoFilesSection
      v-else-if="folderItems && folderItems.length === 0"
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
      :icon="icon"
      :primary-message="primaryMessage"
      :secondary-message="secondaryMessage"
    />
    <ListView
      v-else-if="$store.state.view === 'list'"
      :folder-contents="groupedByFolder"
      :override-can-load-more="overrideCanLoadMore"
      :action-items="actionItems"
      @update-offset="fetchNextPage"
    />
    <GridView
      v-else-if="folderItems && $store.state.view === 'grid'"
      :folder-contents="groupedByFolder"
      :selected-entities="selectedEntities"
      :override-can-load-more="overrideCanLoadMore"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @update-offset="fetchNextPage"
    />
    <EmptyEntityContextMenu
      v-if="showDefaultContextMenu && defaultContextTriggered"
      v-on-outside-click="() => (defaultContextTriggered = false)"
      :close="() => (defaultContextTriggered = false)"
      :action-items="defaultActionItems"
      :event="clickEvent"
    />
    <NewFolderDialog
      v-if="dialog === 'f'"
      v-model="dialog"
      :parent="$route.params.entityName"
      @success="
        () => {
          // Will break if more folders exist than the pagelength
          // Need to check the sort and see where the newly created folder fits
          // And re-fetch that offset
          handleListMutation()
          dialog = null
        }
      "
    />
    <RenameDialog
      v-if="dialog === 'rn'"
      v-model="dialog"
      :entity="selectedEntities[0]"
      @success="
        (data) => {
          handleListMutation(data.name)
          dialog = null
          selectedEntities = []
        }
      "
    />
    <GeneralDialog
      v-if="dialog === 'remove'"
      v-model="dialog"
      :entities="selectedEntities"
      :for="'remove'"
      @success="
        () => {
          handleListMutation()
          dialog = null
          selectedEntities = []
        }
      "
    />
    <GeneralDialog
      v-if="dialog === 'unshare'"
      v-model="dialog"
      :entities="selectedEntities"
      :for="'unshare'"
      @success="
        () => {
          handleListMutation()
          dialog = null
          selectedEntities = []
        }
      "
    />
    <GeneralDialog
      v-if="dialog === 'restore'"
      v-model="dialog"
      :entities="selectedEntities"
      :for="'restore'"
      @success="
        () => {
          handleListMutation()
          dialog = null
          selectedEntities = []
        }
      "
    />
    <ShareDialog
      v-if="dialog === 's'"
      v-model="dialog"
      :entity-name="$store.state.entityInfo[0].name"
    />
    <MoveDialog
      v-if="dialog === 'm'"
      v-model="dialog"
      :entity-name="selectedEntities[0].name"
      @success="
        () => {
          handleListMutation(selectedEntities[0].name)
          dialog = null
          selectedEntities = []
        }
      "
    />
    <DeleteDialog
      v-if="dialog === 'd'"
      v-model="dialog"
      :entities="
        selectedEntities.length > 0
          ? selectedEntities
          : $resources.folderContents.data
      "
      @success="
        () => {
          offset = 0
          folderItems = null
          selectedEntities = []
          fetchNextPage()
          dialog = null
        }
      "
    />
    <CTADeleteDialog
      v-if="dialog === 'cta'"
      v-model="dialog"
      :clear-all="clearAll"
      @success="
        () => {
          offset = 0
          folderItems = null
          selectedEntities = []
          fetchNextPage()
          dialog = null
        }
      "
    />
    <div
      id="selectionElement"
      class="absolute border-1 bg-gray-300 border-gray-400 opacity-50 mix-blend-multiply rounded"
      :style="selectionElementStyle"
      :hidden="!selectionCoordinates.x1"
    />
  </div>
</template>

<script>
import ListView from "@/components/ListView.vue"
import GridView from "@/components/GridView.vue"
import DriveToolBar from "@/components/DriveToolBar.vue"
import NoFilesSection from "@/components/NoFilesSection.vue"
import NewFolderDialog from "@/components/NewFolderDialog.vue"
import RenameDialog from "@/components/RenameDialog.vue"
import ShareDialog from "@/components/ShareDialog/ShareDialog.vue"
import GeneralDialog from "@/components/GeneralDialog.vue"
import DeleteDialog from "@/components/DeleteDialog.vue"
import CTADeleteDialog from "@/components/CTADeleteDialog.vue"
import MoveDialog from "../components/MoveDialog.vue"
import FolderContentsError from "@/components/FolderContentsError.vue"
import EntityContextMenu from "@/components/EntityContextMenu.vue"
import EmptyEntityContextMenu from "@/components/EmptyEntityContextMenu.vue"
import { formatSize, formatDate } from "@/utils/format"
import { getLink } from "@/utils/getLink"
import { useTimeAgo } from "@vueuse/core"
import { toggleFav, clearRecent } from "@/resources/files"

import { selectedEntitiesDownload } from "@/utils/download"
import { RotateCcw } from "lucide-vue-next"
import NewFolder from "./EspressoIcons/NewFolder.vue"
import FileUpload from "./EspressoIcons/File-upload.vue"
import FolderUpload from "./EspressoIcons/Folder-upload.vue"
import Share from "./EspressoIcons/Share.vue"
import Download from "./EspressoIcons/Download.vue"
import Link from "./EspressoIcons/Link.vue"
import Rename from "./EspressoIcons/Rename.vue"
import Move from "./EspressoIcons/Move.vue"
import Info from "./EspressoIcons/Info.vue"
import Preview from "./EspressoIcons/Preview.vue"
import Trash from "./EspressoIcons/Trash.vue"
import NewFile from "./EspressoIcons/NewFile.vue"
import { toast } from "../utils/toasts.js"
import { capture } from "@/telemetry"
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect"
import { getEntities } from "@/resources/files"

export default {
  name: "PageGeneric",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    NewFolderDialog,
    RenameDialog,
    MoveDialog,
    DeleteDialog,
    ShareDialog,
    GeneralDialog,
    FolderContentsError,
    EntityContextMenu,
    EmptyEntityContextMenu,
    CTADeleteDialog,
  },
  props: {
    url: {
      type: String,
      default: "",
      required: false,
    },
    parent: {
      type: String,
      default: null,
      required: false,
    },
    showDefaultContextMenu: {
      type: Boolean,
      default: false,
      required: false,
    },
    isSharedFolder: {
      type: Boolean,
      default: false,
      required: false,
    },
    isActive: {
      type: Number,
      default: 1,
      required: false,
    },
    showSort: {
      type: Boolean,
      default: false,
      required: false,
    },
    entityName: {
      type: String,
      required: false,
      default: "",
    },
    icon: {
      type: Object,
      default: null,
    },
    primaryMessage: {
      type: String,
      required: false,
      default: "No Files here",
    },
    secondaryMessage: {
      type: String,
      required: false,
      default: "Add files",
    },
    recents: {
      type: Boolean,
      required: false,
      default: false,
    },
    favourites: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data: () => ({
    getEntities,
    clickEvent: null,
    folderItems: null,
    previewEntity: null,
    dialog: "",
    defaultContextTriggered: false,
    pageLength: 60,
    pageOffset: 0,
    overrideCanLoadMore: false,
    clearAll: false,
    selectionElementStyle: {},
    selectionCoordinates: { x1: 0, x2: 0, y1: 0, y2: 0 },
    containerRect: null,
    selectedIDs: null,
  }),

  computed: {
    groupedByFolder() {
      let output = {}
      if (this.recents && this.folderItems) {
        output = this.groupByAccessed(this.folderItems)
      } else if (this.folderItems && this.foldersBefore) {
        const folders = this.folderItems.filter((x) => x.is_group === 1)
        const files = this.folderItems.filter((x) => x.is_group === 0)
        if (folders.length > 0) {
          output.Folders = folders
        }
        if (files.length > 0) {
          output.Files = files
        }
      } else {
        output = { "All Files": this.folderItems }
      }
      return output
    },
    selectedEntities: {
      get() {
        return this.$store.state.entityInfo
      },
      set(val) {
        this.$store.commit("setEntityInfo", val)
      },
    },
    filters() {
      return this.$store.state.activeFilters
    },
    tags() {
      const activeTags = this.$store.state.activeTags
      const tagNames = []
      activeTags.map((tag) => tagNames.push(tag.name))
      return tagNames
    },
    orderBy() {
      return this.$store.state.sortOrder.ascending
        ? this.$store.state.sortOrder.field
        : `${this.$store.state.sortOrder.field} desc`
    },
    userId() {
      return this.$store.state.auth.user_id
    },
    columnHeaders() {
      return [
        {
          label: "Name",
          field: "title",
          sortable: true,
        },
        {
          label: "Owner",
          field: "owner",
          sortable: true,
        },
        {
          label: "Modified",
          field: "modified",
          sortable: true,
        },
        {
          label: "Size",
          field: "file_size",
          sortable: true,
        },
        {
          label: "Type",
          field: "mime_type",
          sortable: true,
        },
      ].filter((item) => item.sortable)
    },
    defaultActionItems() {
      return [
        {
          label: "Upload File",
          icon: FileUpload,
          handler: () => this.emitter.emit("uploadFile"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "Upload Folder",
          icon: FolderUpload,
          handler: () => this.emitter.emit("uploadFolder"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "New Folder",
          icon: NewFolder,
          handler: () => (this.dialog = "f"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "New Document",
          icon: NewFile,
          handler: () => this.newDocument(),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "New Whiteboard",
          icon: NewFile,
          handler: () => this.newWhiteboard(),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        /*{
          label: "Paste",
          icon: "clipboard",
          handler: async () => {
            this.pasteEntities()
          },
          isEnabled: () => this.$store.state.pasteData.entities.length,
        },*/
      ].filter((a) => !a.isEnabled || a.isEnabled())
    },
    actionItems() {
      if (this.$route.name === "Trash") {
        return [
          {
            label: "Restore",
            icon: RotateCcw,
            onClick: () => (this.dialog = "restore"),
          },
          {
            label: "Delete forever",
            icon: Trash,
            onClick: () => (this.dialog = "d"),
            isEnabled: () => this.$route.name === "Trash",
          },
        ].filter((a) => !a.isEnabled || a.isEnabled())
      } else {
        return [
          {
            label: "Preview",
            icon: Preview,
            onClick: ([entity]) => this.openEntity(entity),
            important: true,
          },
          {
            label: "Download",
            icon: Download,
            onClick: selectedEntitiesDownload,
            isEnabled: (e) =>
              e.allow_download || e.owner === "You" || e.owner.label === "You",
            multi: true,
            important: true,
          },
          {
            label: "Share",
            icon: Share,
            onClick: () => (this.dialog = "s"),
            isEnabled: (e) =>
              e.owner === "You" || e.owner.label === "You" || e.share,
            important: true,
          },
          {
            label: "Get Link",
            icon: Link,
            onClick: ([entity]) => getLink(entity),
            important: true,
          },
          {
            label: "Rename",
            icon: Rename,
            onClick: () => (this.dialog = "rn"),
            isEnabled: (e) =>
              e.write || e.owner === "You" || e.owner.label === "You",
          },
          {
            label: "Move",
            icon: Move,
            onClick: () => (this.dialog = "m"),
            isEnabled: (e) => e.owner === "You" || e.owner.label === "You",
            multi: true,
          },
          /* {
            label: "Duplicate",
            icon: Copy,
            onClick: () => {
              this.$store.commit("setPasteData", {
                entities: this.selectedEntities.map((x) => x.name),
                action: "copy",
              })
            },
            isEnabled: () => {
              return (
                this.selectedEntities.length > 0 &&
                (this.selectedEntities[0].write ||
                  this.selectedEntities[0].owner === "You")
              )
            },
          }, */
          {
            label: "Show Info",
            icon: Info,
            onClick: () => this.$store.commit("setShowInfo", true),
            isEnabled: () => !this.$store.state.showInfo,
            important: true,
          },
          {
            label: "Hide Info",
            icon: Info,
            onClick: () => this.$store.commit("setShowInfo", false),
            isEnabled: () => this.$store.state.showInfo,
            important: true,
          },
          /*{
            label: "Paste",
            icon: "clipboard",
            onClick: async () => {
              this.pasteEntities(this.selectedEntities[0].name)
            },
            isEnabled: () => {
              return (
                this.$store.state.pasteData.entities.length &&
                this.selectedEntities.length === 1 &&
                this.selectedEntities[0].is_group
              )
            },
          },*/
          {
            label: "Favourite",
            icon: "star",
            onClick: (entities) =>
              toggleFav.submit({
                entities,
              }),
            isEnabled: (e, multi) => !e.is_favourite || multi,
            important: true,
            multi: true,
          },
          {
            label: "Unfavourite",
            icon: "star",
            onClick: (entities) =>
              toggleFav.submit({
                entities: entities.map((e) => ({
                  name: e.name,
                  is_favourite: false,
                })),
              }),
            isEnabled: (e) => e.is_favourite,
            important: true,
            multi: true,
          },
          // {
          //   label: "Color",
          //   isEnabled: (e) => e.is_group && (e.write || e.owner === "You" || e.owner.label === "You"),
          // },
          {
            label: "Remove from Recents",
            icon: "clock",
            onClick: (entities) =>
              clearRecent.submit(
                {
                  entities,
                },
                {
                  onSuccess: () =>
                    entities.length > 1
                      ? toast(`Cleared  ${entities.length} files from Recents`)
                      : null,
                }
              ),
            isEnabled: () => this.$route.name === "Recents",
            important: true,
            multi: true,
          },
          {
            label: "Unshare",
            danger: true,
            icon: "trash-2",
            onClick: () => (this.dialog = "unshare"),
            isEnabled: (e) =>
              e.owner != "You" &&
              e.user_doctype === "User" &&
              e.everyone !== 1 &&
              !this.isSharedFolder,
          },
          {
            label: "Move to Trash",
            icon: Trash,
            danger: true,
            onClick: () => (this.dialog = "remove"),
            isEnabled: (e) => e.owner === "You" || e.owner.label === "You",
            important: true,
            multi: true,
          },
        ]
      }
    },
    foldersBefore() {
      return this.$store.state.foldersBefore
    },
  },
  watch: {
    filters: {
      handler() {
        this.pageOffset = 0
        this.resetAndFetch()
      },
      deep: true,
    },
    tags: {
      handler() {
        this.pageOffset = 0
        this.resetAndFetch()
      },
      deep: true,
    },
    folderItems: {
      handler(newVal) {
        this.$store.commit("setCurrentViewEntites", newVal)
      },
    },
    orderBy: {
      handler() {
        this.pageOffset = 0
        this.resetAndFetch()
      },
    },
  },
  mounted() {
    getEntities.update({
      params: {
        entity_name: this.entityName,
        order_by: this.orderBy,
        offset: this.pageOffset,
        limit: this.pageLength,
        folders_first: this.foldersBefore,
        is_active: this.isActive,
        recents_only: this.recents,
        favourites_only: this.favourites,
        file_kind_list: JSON.stringify(this.filters),
        tag_list: JSON.stringify(this.tags),
      },
    })
    this.fetchNextPage()
    this.emitter.on("fetchFolderContents", () => {
      this.handleListMutation()
    })
    this.emitter.on("showCTADelete", () => {
      this.clearAll = true
      this.dialog = "cta"
    })
    this.emitter.on("showShareDialog", () => (this.dialog = "s"))
    this.emitter.on("selectAll", () => {
      this.clearAll()
    })
    this.emitter.on("createNewDocument", () => {
      this.newDocument()
    })

    this.pasteListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "v" || e.key === "V") &&
        this.$store.state.pasteData.entities.length
      )
        this.pasteEntities()
    }
    window.addEventListener("keydown", this.pasteListener)

    this.deleteListener = (e) => {
      if (e.key === "Delete" && this.selectedEntities.length)
        this.dialog = "remove"
    }
    window.addEventListener("keydown", this.deleteListener)

    window.addEventListener(
      "dragover",
      function (e) {
        e = e || event
        e.preventDefault()
      },
      false
    )
    window.addEventListener(
      "drop",
      function (e) {
        e = e || event
        e.preventDefault()
      },
      false
    )
    this.$store.commit("setHasWriteAccess", true)
    window.addEventListener("scroll", this.onScroll)
    if (this.isEmpty) return
    this.updateContainerRect()
    visualViewport.addEventListener("resize", this.updateContainerRect)
  },
  unmounted() {
    this.folderItems = []
    this.pageOffset = 0
    this.emitter.off("fetchFolderContents")
    this.$store.commit("setHasWriteAccess", false)
    window.removeEventListener("keydown", this.pasteListener)
    window.removeEventListener("keydown", this.deleteListener)
    window.removeEventListener("scroll", this.onScroll)
    document.removeEventListener("keydown", this.selectAllListener)
    document.removeEventListener("keydown", this.copyListener)
    document.removeEventListener("keydown", this.cutListener)
  },
  methods: {
    handleContextMenu(event) {
      this.clickEvent = event
      this.defaultContextTriggered = true
      event.preventDefault()
    },
    dragSelectStart(event) {
      this.selectedIDs = null
      document.addEventListener("mousemove", this.dragSelectMove)
      document.addEventListener("mouseup", this.dragSelectStop)
      this.selectionCoordinates.x1 = event.clientX
      this.selectionCoordinates.y1 = event.clientY
      this.selectionCoordinates.x2 = event.clientX
      this.selectionCoordinates.y2 = event.clientY
      this.selectionElementStyle = calculateRectangle(this.selectionCoordinates)
    },
    dragSelectMove(event) {
      if (this.isEmpty) return
      if (event.which != 1 || !this.selectionCoordinates.x1) return
      this.selectionCoordinates.x2 = Math.max(
        this.containerRect.left,
        Math.min(this.containerRect.right, event.clientX)
      )
      this.selectionCoordinates.y2 = Math.max(
        this.containerRect.top,
        Math.min(this.containerRect.bottom, event.clientY)
      )
      this.selectionElementStyle = calculateRectangle(this.selectionCoordinates)
      const entityElements = this.$el.querySelectorAll(".entity")
      const selectedEntities = handleDragSelect(
        entityElements,
        this.selectionCoordinates,
        this.folderContents
      )
      this.selectedIDs = selectedEntities
    },
    dragSelectStop() {
      if (this.selectedIDs) {
        this.selectedEntities = this.folderItems.filter((item) =>
          this.selectedIDs.has(item.name)
        )
      }
      this.selectionCoordinates = { x1: 0, x2: 0, y1: 0, y2: 0 }
      document.removeEventListener("mousemove", this.dragSelectMove)
      document.removeEventListener("mouseup", this.dragSelectStop)
    },
    updateContainerRect() {
      this.containerRect = this.$refs["container"]?.getBoundingClientRect()
    },
    /* onScroll() {
      const position = window.pageYOffset
      this.$store.dispatch("saveScrollPosition", {
        route: this.$route.fullPath,
        position,
      })
    }, */
    fetchNextPage() {
      this.pageOffset = this.pageOffset + this.pageLength
      getEntities.submit({ pageOffset: this.pageOffset }).then((data) => {
        this.overrideCanLoadMore = data.length < 60 ? false : true
        this.folderItems = this.folderItems
          ? this.folderItems.concat(data)
          : data
      })
      // this.$resources.folderContents.fetch().then((data) => {
      //   this.overrideCanLoadMore = data.length < 60 ? false : true
      //   this.folderItems = this.folderItems
      //     ? this.folderItems.concat(data)
      //     : data
      // })
    },
    resetAndFetch() {
      this.folderItems = null
      this.$resources.folderContents
        .fetch({
          entity_name: this.entityName,
          order_by: this.orderBy,
          offset: 0,
          limit: this.pageLength,
          is_active: this.isActive,
          folders_first: this.foldersBefore,
          recents_only: this.recents,
          favourites_only: this.favourites,
          file_kind_list: JSON.stringify(this.filters),
          tag_list: JSON.stringify(this.tags),
        })
        .then((data) => {
          this.pageOffset = data.length
          this.folderItems = data
          this.overrideCanLoadMore = data.length < 60 ? false : true
        })
    },
    handleListMutation(entityID) {
      let index = this.folderItems.findIndex((obj) => obj.name === entityID)
      let entityPage = Math.ceil(index / this.pageLength)
      let entityOriginalOffset = Math.max(
        0,
        entityPage * this.pageLength - this.pageLength
      )

      let endIndex = this.folderItems.findIndex(
        (obj) =>
          obj.name ===
          this.$store.state.entityInfo[this.$store.state.entityInfo.length - 1]
      )
      let endPage = Math.ceil(endIndex / this.pageLength)
      let endtityOgOffset = Math.max(
        0,
        endPage * this.pageLength - this.pageLength
      )
      this.$resources.folderContents
        .fetch({
          entity_name: this.entityName,
          order_by: this.orderBy,
          offset: entityOriginalOffset,
          limit: this.pageLength,
          folders_first: this.foldersBefore,
          is_active: this.isActive,
          recents_only: this.recents,
          favourites_only: this.favourites,
          file_kind_list: JSON.stringify(this.filters),
          tag_list: JSON.stringify(this.tags),
        })
        .then((data) => {
          this.folderItems.splice(
            entityOriginalOffset,
            entityOriginalOffset + this.pageLength,
            ...data
          )
        })
    },
    openEntity(entity) {
      if (this.$route.name === "Trash") {
        return
      }
      if (entity.is_group) {
        this.$router.push({
          name: "Folder",
          params: { entityName: entity.name },
        })
      } else if (entity.mime_type === "frappe_doc") {
        if (this.$store.state.editorNewTab) {
          window.open(
            this.$router.resolve({
              name: "Document",
              params: { entityName: entity.name },
            }).href,
            "_blank"
          )
        } else {
          this.$router.push({
            name: "Document",
            params: { entityName: entity.name },
          })
        }
      } else if (entity.mime_type === "frappe_whiteboard") {
        this.$router.push({
          name: "Whiteboard",
          params: { entityName: entity.name },
        })
      } else {
        this.$router.push({
          name: "File",
          params: { entityName: entity.name },
        })
        this.previewEntity = entity
      }
    },
    async pasteEntities(newParent = this.$store.state.currentFolderID) {
      const method =
        this.$store.state.pasteData.action === "cut" ? "move" : "copy"
      for (let i = 0; i < this.$store.state.pasteData.entities.length; i++) {
        await this.$resources.pasteEntity.submit({
          method,
          entity_name: this.$store.state.pasteData.entities[i],
          new_parent: newParent,
        })
      }
      this.selectedEntities = []
      this.$store.commit("setPasteData", { entities: [], action: null })
      this.$resources.folderContents.fetch()
    },
    async newDocument() {
      await this.$resources.createDocument.submit({
        title: "Untitled Document",
        content: null,
        parent: this.$store.state.currentFolderID,
      })
      capture("new_document_created")
      if (this.$store.state.editorNewTab) {
        window.open(
          this.$router.resolve({
            name: "Document",
            params: { entityName: this.previewEntity.name },
          }).href,
          "_blank"
        )
      } else {
        this.$router.push({
          name: "Document",
          params: { entityName: this.previewEntity.name },
        })
      }
    },
    async newWhiteboard() {
      console.log(this.$store.state.currentFolderID)
      await this.$resources.createWhiteboard.submit({
        title: "Untitled Whiteboard",
        content: null,
        parent: this.$store.state.currentFolderID,
      })
      if (this.$store.state.editorNewTab) {
        window.open(
          this.$router.resolve({
            name: "Whiteboard",
            params: { entityName: this.previewEntity.name },
          }).href,
          "_blank"
        )
      } else {
        this.$router.push({
          name: "Whiteboard",
          params: { entityName: this.previewEntity.name },
        })
      }
    },
    groupByAccessed(entities) {
      const today = new Date()
      const grouped = {
        Today: [],
        "Earlier this week": [],
        "Earlier this month": [],
        "Earlier this year": [],
        "Older than a year": [],
      }
      entities.forEach((file) => {
        const modifiedDate = new Date(file.modified)
        const yearDiff = today.getFullYear() - modifiedDate.getFullYear()
        const monthDiff =
          today.getMonth() - modifiedDate.getMonth() + yearDiff * 12 // Adjust for year difference
        const dayDiff = Math.floor(
          (today - modifiedDate) / (1000 * 60 * 60 * 24)
        )
        if (dayDiff === 0) {
          grouped["Today"].push(file)
        } else if (dayDiff <= 7) {
          grouped["Earlier this week"].push(file)
        } else if (monthDiff === 0) {
          grouped["Earlier this month"].push(file)
        } else if (yearDiff === 0) {
          grouped["Earlier this year"].push(file)
        } else {
          grouped["Older than a year"].push(file)
        }
      })
      return grouped
    },
  },
  resources: {
    pasteEntity() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        auto: false,
      }
    },
    folderContents() {
      return {
        method: "GET",
        url: this.url,
        cache: "folder-contents",
        auto: false,
        params: {
          entity_name: this.entityName || "",
          order_by: this.orderBy,
          offset: this.pageOffset,
          limit: this.pageLength,
          folders_first: this.foldersBefore,
          is_active: this.isActive,
          recents_only: this.recents,
          favourites_only: this.favourites,
          file_kind_list: JSON.stringify(this.filters),
          tag_list: JSON.stringify(this.tags),
        },
        transform(data) {
          this.$resources.folderContents.error = null
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size
            if (entity.is_group) {
              if (entity.item_count === 0 || entity.item_count > 0) {
                entity.file_size = entity.item_count + " item"
                if (entity.item_count > 1) {
                  entity.file_size = entity.item_count + " items"
                }
              } else {
                entity.file_size = ""
              }
            } else {
              entity.file_size = formatSize(entity.file_size)
            }
            entity.relativeModified = useTimeAgo(entity.modified)
            entity.modified = formatDate(entity.modified)
            entity.creation = formatDate(entity.creation)
            entity.owner =
              entity.owner === this.userId ? "You" : entity.full_name
          })
        },
        onError(error) {
          if (error && error.exc_type === "PermissionError") {
            this.$store.commit("setError", {
              primaryMessage: "Forbidden",
              secondaryMessage: "Insufficient permissions for this resource",
            })
            this.$router.replace({ name: "Error" })
          }
        },
      }
    },
    toggleFavourite() {
      return {
        method: "POST",
        auto: false,
        url: "drive.api.files.add_or_remove_favourites",
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities?.map((entity) => entity.name)
          ),
        },
        onSuccess() {
          // Toggled OFF
          console.log(this.selectedEntities[0].is_favourite)
          if (this.selectedEntities[0].is_favourite === false) {
            toast({
              title: `${
                this.selectedEntities.length > 1
                  ? this.selectedEntities.length + " items removed"
                  : "Removed"
              } from Favourites`,
              position: "bottom-right",
              timeout: 2,
            })
          } else {
            toast({
              title: `${
                this.selectedEntities.length > 1
                  ? this.selectedEntities.length + " items added"
                  : "Added"
              } to Favourites`,
              position: "bottom-right",
              timeout: 2,
            })
          }
          this.handleListMutation(this.selectedEntities[0].name)
        },
      }
    },
    createDocument() {
      return {
        method: "POST",
        url: "drive.api.files.create_document_entity",
        onSuccess(data) {
          data.modified = formatDate(data.modified)
          data.creation = formatDate(data.creation)
          this.$store.commit("setEntityInfo", [data])
          this.previewEntity = data
          data.owner = "You"
        },
        onError(error) {
          console.log(error.messages)
        },
        auto: false,
      }
    },
    createWhiteboard() {
      return {
        method: "POST",
        url: "drive.api.files.create_whiteboard_entity",
        onSuccess(data) {
          data.modified = formatDate(data.modified)
          data.creation = formatDate(data.creation)
          this.$store.commit("setEntityInfo", [data])
          this.previewEntity = data
          data.owner = "You"
        },
        onError(error) {
          console.log(error)
        },
        auto: false,
      }
    },
  },
}
</script>

<style>
html {
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
</style>
