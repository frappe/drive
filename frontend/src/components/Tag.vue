<template>
  <Popover transition="default">
    <template #target="{ togglePopover }">
      <Badge
        :color="tag.color"
        class="h-6 cursor-pointer"
        :style="{ fontSize: '12px', cursor: 'pointer' }"
        @click="togglePopover()">
        {{ `• ${tag.title}` }}
      </Badge>
    </template>
    <template #body-main="{ togglePopover }">
      <div class="p-1 space-x-1 flex">
        <button
          v-for="color in colors"
          :class="`h-4 w-4 rounded-full bg-${color}-500`"
          @click="
            $resources.updateColor.submit({
              tag: tag.name,
              color: color,
            });
            togglePopover();
          " />
      </div>
    </template>
  </Popover>
</template>

<script>
import { Badge, Popover } from "frappe-ui";

export default {
  name: "Tag",

  data() {
    return {
      colors: ["blue", "green", "yellow", "red", "gray"],
    };
  },

  components: {
    Popover,
    Badge,
  },

  emits: ["success"],

  props: {
    tag: {
      type: Object,
      required: true,
    },
  },

  resources: {
    updateColor() {
      return {
        url: "drive.api.tags.update_tag_color",
        onSuccess() {
          this.$emit("success");
        },
      };
    },
  },
};
</script>
