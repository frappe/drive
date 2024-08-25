<template>
  <div class="flex px-3 bg-white pb-2 shadow-sm">
    <Dropdown :options="fileMenuOptions">
      <template #default="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]"
        >
          File
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'New',
          hideLabel: true,
          items: [
            {
              label: 'Undo',
              handler: () => alert('New File'),
            },
            {
              label: 'Redo',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Cut',
              handler: () => alert('New File'),
            },
            {
              label: 'Copy',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Paste',
              handler: () => alert('New File'),
            },
            {
              label: 'Paste without Formatting',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Select All',
              handler: () => alert('New File'),
            },
            {
              label: 'Find and Replace',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
          ],
        },
      ]"
    >
      <template #default="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]"
        >
          Edit
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'New',
          hideLabel: true,
          items: [
            {
              label: 'Mode',
              handler: () => alert('New File'),
            },
            {
              label: 'Text Width',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Focus Mode',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Full screen',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
          ],
        },
      ]"
    >
      <template #default="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]"
        >
          View
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'Insert',
          hideLabel: true,
          items: [
            {
              label: 'Image',
              handler: () => alert('New File'),
            },
            {
              label: 'Video',
              handler: () => alert('New File'),
            },
            {
              label: 'Table',
              handler: () => alert('New File'),
            },
            {
              label: 'Link',
              handler: () => alert('New File'),
            },
            {
              label: 'Horizontal Line',
              handler: () => alert('New File'),
            },
            {
              label: 'Emoji',
              handler: () => alert('New File'),
            },
            {
              label: 'Blockquote',
              handler: () => alert('New File'),
            },
          ],
        },
      ]"
    >
      <template #default="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]"
        >
          Insert
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'New',
          hideLabel: true,
          items: [
            {
              label: 'Text',
              handler: () => alert('New File'),
            },
            {
              label: 'Style',
              handler: () => alert('New File'),
            },
            {
              label: 'Alignment',
              handler: () => alert('New File'),
            },
            {
              label: 'Line Height',
              handler: () => alert('New File'),
            },
            {
              label: 'Horizontal Line',
              handler: () => alert('New File'),
            },
            {
              label: 'List and Numbering',
              handler: () => alert('New File'),
            },
            {
              label: 'Table',
              handler: () => alert('New File'),
            },
          ],
        },
      ]"
    >
      <template #default="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]"
        >
          Format
        </button>
      </template>
    </Dropdown>
    <!--     <div class="ml-auto">
      <Dropdown :options="modeMenuOptions">
        <template v-slot="{ open }">
          <Button :icon-left="modeButtonIcon" :label="modeButtonText" />
        </template>
      </Dropdown>
    </div> -->
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="entityName"
    />
    <!-- Ideally convert the component to recieve both an array or a single entity -->
    <GeneralDialog
      v-model="showRemoveDialog"
      :entities="entityName"
      :for="'remove'"
      @success="
        () => {
          $router.go(-1)
        }
      "
    />
  </div>
</template>

<script>
import { Dropdown } from "frappe-ui"
import ShareDialog from "@/components/ShareDialog.vue"
import GeneralDialog from "@/components/GeneralDialog.vue"

export default {
  name: "MenuBar",
  components: {
    Dropdown,
    ShareDialog,
    GeneralDialog,
  },
  props: {
    entityName: {
      default: "",
      type: String,
      required: false,
    },
    editable: {
      type: Boolean,
      required: false,
    },
    isCommentModeOn: {
      type: Boolean,
      required: false,
    },
    isReadOnly: {
      type: Boolean,
      required: false,
    },
  },
  emits: ["toggleCommentMode", "toggleEditMode", "toggleReadMode"],
  data() {
    return {
      showShareDialog: false,
      showRemoveDialog: false,
      modeButtonIcon: "",
      fileMenuOptions: [
        /*         {
          group: "New",
          hideLabel: true,
          items: [
            {
              icon: "file-plus",
              label: "New File",
              handler: () => this.emitter.emit("createNewDocument"),
            },
          ],
        }, */
        {
          group: "Current File",
          hideLabel: true,
          items: [
            /* Look into making a modal/dialog/portal for this and opening a file from the current file view*/
            /* {
              icon: "copy",
              label: "Copy File",
              handler: () =>
                this.$store.commit("setPasteData", {
                  entities: this.entityName,
                  action: "copy",
                }),
            }, */
            {
              icon: "share-2",
              label: "Share File",
              handler: () => (this.showShareDialog = true),
            },
            {
              icon: "star",
              label: "Add to favourites",
              handler: () => alert("Open File"),
            },
          ],
        },
        {
          group: "Delete",
          hideLabel: true,
          items: [
            {
              icon: "trash-2",
              label: "Delete File",
              handler: () => (this.showRemoveDialog = true),
            },
          ],
        },
      ],
      modeMenuOptions: [
        {
          group: "Mode",
          hideLabel: true,
          items: [
            {
              icon: "eye",
              label: "Reading",
              handler: () => {
                this.emitter.emit("toggleReadMode")
              },
            },
            {
              icon: "edit-3",
              label: "Editing",
              handler: () => {
                this.emitter.emit("toggleEditMode")
              },
            },
            {
              icon: "message-square",
              label: "Suggesting",
              handler: () => {
                this.emitter.emit("toggleCommentMode")
              },
            },
          ],
        },
      ],
    }
  },
  computed: {
    modeButtonText() {
      if (this.editable) {
        this.modeButtonIcon = "edit-3"
        return "Editing"
      } else if (this.isReadOnly) {
        this.modeButtonIcon = "eye"
        return "Reading"
      } else if (this.isCommentModeOn) {
        this.modeButtonIcon = "message-square"
        return "Suggesting"
      }
    },
  },
}
</script>
