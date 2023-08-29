<template>
  <Popover
    trigger="hover"
    placement="right-start"
    :hover-delay="0.5"
    :leave-delay="0.5">
    <template #target="{ togglePopover, isOpen }">
      <div
        :active="isOpen"
        class="h-6 hover:bg-gray-100 text-sm cursor-pointer rounded-[7px] flex px-1 items-center cursor-pointer"
        @click="togglePopover()">
        <FeatherIcon
          name="droplet"
          class="stroke-1.5 w-4 h-4 text-gray-700 mr-3" />
        <div class="text-gray-800">Change Color</div>
        <FeatherIcon
          :name="'chevron-right'"
          class="w-4 h-4 text-gray-700 ml-16" />
      </div>
    </template>
    <template #body-main>
      <div class="grid grid-cols-5 gap-2 p-3">
        <button
          v-for="color in colors"
          :key="color"
          class="h-6 w-6 rounded-full justify-self-center"
          :style="{ backgroundColor: color }"
          @click="
            $resources.updateColor.submit({
              method: 'change_color',
              entity_name: entityName,
              new_color: color,
            })
          " />
      </div>
    </template>
  </Popover>
</template>

<script>
import { Popover, FeatherIcon } from "frappe-ui";

export default {
  name: "ColorPopover",
  components: { Popover, FeatherIcon },
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
    };
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
            return "New name is required";
          }
        },
        onSuccess() {
          this.emitter.emit("fetchFolderContents");
        },
      };
    },
  },
};
</script>
