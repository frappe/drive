<template>
  <Popover
    trigger="hover"
    placement="right-start"
    :hover-delay="0.5"
    :leave-delay="0.5">
    <template #target="{ togglePopover, isOpen }">
      <div
        :active="isOpen"
        class="h-7 flex items-center hover:bg-gray-100 rounded-lg px-3 cursor-pointer"
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
import { theme } from "@/utils/theme";

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
        "slate",
        "gray",
        "zinc",
        "neutral",
        "stone",
        "red",
        "orange",
        "amber",
        "yellow",
        "lime",
        "green",
        "emerald",
        "teal",
        "cyan",
        "sky",
        "blue",
        "indigo",
        "violet",
        "purple",
        "fuchsia",
      ].map((color) => theme.colors[color]["500"]),
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
