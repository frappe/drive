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
      <div class="bg-white rounded-xl shadow-md p-1 z-10 space-y-0.5 border">
        <div
          v-for="item in tagActions"
          class="hover:bg-gray-100 cursor-pointer rounded-lg flex items-center px-1 py-0.5"
          @click="
            item.handler();
            togglePopover();
          ">
          <FeatherIcon :name="item.icon" class="w-3 h-3 text-gray-700 mr-1" />
          <div class="text-gray-800 text-xs">{{ item.label }}</div>
        </div>
        <!-- <button
          v-for="color in colors"
          :class="`h-4 w-4 rounded-full bg-${color}-500`"
          @click="
            $resources.updateColor.submit({
              tag: tag.name,
              color: color,
            });
            togglePopover();
          " /> -->
      </div>
    </template>
  </Popover>
</template>

<script>
import { Badge, Popover, FeatherIcon } from "frappe-ui";

export default {
  name: "Tag",

  data() {
    return {
      colors: ["blue", "green", "yellow", "red", "gray"],
      tagActions: [
        {
          label: "Color",
          icon: "droplet",
        },
        {
          label: "Remove",
          icon: "x",
          handler: () => {
            this.$resources.removeTag.submit();
          },
        },
        {
          label: "Delete",
          icon: "trash",
          handler: () => {
            this.$resources.deleteTag.submit();
          },
        },
      ],
    };
  },

  components: {
    Popover,
    Badge,
    FeatherIcon,
  },

  emits: ["success"],

  props: {
    entity: {
      type: String,
      required: true,
    },
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

    removeTag() {
      return {
        url: "drive.api.tags.remove_tag",
        params: {
          entity: this.entity,
          tag: this.tag.name,
        },
        onSuccess() {
          this.$emit("success");
        },
      };
    },

    deleteTag() {
      return {
        url: "drive.api.tags.delete_tag",
        params: {
          tag: this.tag.name,
        },
        onSuccess() {
          this.$emit("success");
        },
      };
    },
  },
};
</script>
