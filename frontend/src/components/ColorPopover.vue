<template>
  <Popover
    trigger="hover"
    placement="right-start"
    popover-class="border-x-[8px] border-transparent"
    :hover-delay="0.25"
    :leave-delay="0.5"
  >
    <template #target="{ togglePopover, isOpen }">
      <div
        :active="isOpen"
        class="h-6 px-2 hover:bg-gray-100 text-sm cursor-pointer rounded-[5px] flex justify-start items-center w-full"
        @click="togglePopover()"
      >
        <Palette class="h-4 w-auto mr-2 text-gray-800" />
        <div class="text-gray-800">Color</div>
        <FeatherIcon
          :name="'chevron-right'"
          class="h-3.5 text-gray-900 ml-auto"
        />
      </div>
    </template>
    <template #body-main>
      <div class="grid grid-cols-5 gap-2 p-3">
        <button
          v-for="color in colors"
          :key="color"
          class="h-5 w-5 rounded-full justify-self-center"
          :style="{ backgroundColor: color }"
          @click="
            $resources.updateColor.submit({
              method: 'change_color',
              entity_name: entityName,
              new_color: color,
            })
          "
        />
      </div>
    </template>
  </Popover>
</template>

<script>
import { Popover, FeatherIcon } from "frappe-ui"
import Palette from "./EspressoIcons/Palette.vue"

export default {
  name: "ColorPopover",
  components: { Popover, FeatherIcon, Palette },
  props: {
    entityName: {
      type: String,
      default: null,
    },
  },
  emits: ["success"],
  data() {
    return {
      colors: [
        "#525252",
        "#775225",
        "#e11d48",
        "#20C1F4",
        "#2374D2",
        "#fbbf24",
        "#E39B4C",
        "#16a34a",
        "#EF7323",
        "#9333ea",
      ],
    }
  },
  resources: {
    updateColor() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          method: "change_color",
          entity_name: this.entityName,
        },
        validate(params) {
          if (!params?.new_color) {
            return "New name is required"
          }
        },
        onSuccess() {
          this.emitter.emit("fetchFolderContents")
        },
      }
    },
  },
}
</script>
