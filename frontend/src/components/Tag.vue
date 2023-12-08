<template>
  <Popover transition="default">
    <template #target="{ togglePopover }">
      <Badge
        class="text-xs font-medium px-2"
        variant="subtle"
        :theme="`${tag.color}`"
        :style="{
          cursor: entity.owner === 'Me' ? 'pointer' : 'default',
        }"
        @click="if (entity.owner === 'Me') togglePopover();">
        {{ `${tag.title}` }}
        <FeatherIcon
          v-if="entity.owner === 'Me'"
          @click="$resources.removeTag.submit()"
          class="my-auto h-3 stroke-2"
          name="x" />
      </Badge>
    </template>
    <template #body-main="{ togglePopover }">
      <div class="bg-white rounded shadow-md p-1 z-10 space-y-0.5 absolute">
        <Popover
          placement="right"
          trigger="hover"
          :hover-delay="0.5"
          :leave-delay="0.6">
          <template #target>
            <div
              class="hover:bg-gray-100 cursor-pointer rounded flex items-center px-1.5 py-1 w-24">
              <FeatherIcon name="droplet" class="w-4 h-4 text-gray-700 mr-1" />
              <div class="text-gray-800 text-base">Color</div>
              <FeatherIcon
                name="chevron-right"
                class="w-4 h-4 text-gray-700 ml-auto" />
            </div>
          </template>
          <template #body-main="{ togglePopover: toggleColors }">
            <div class="p-1 space-x-1 flex">
              <button
                v-for="color in colors"
                :key="color"
                :class="`h-5 w-5 rounded-full bg-${
                  color === 'orange' ? 'amber' : color
                }-600`"
                @click="
                  $resources.updateColor.submit({
                    tag: tag.name,
                    color: color,
                  });
                  toggleColors();
                " />
            </div>
          </template>
        </Popover>
        <div
          v-for="item in tagActions"
          :key="item"
          class="hover:bg-gray-100 cursor-pointer rounded flex items-center px-1.5 py-1 w-24"
          @click="
            item.handler();
            togglePopover();
          ">
          <FeatherIcon :name="item.icon" class="w-4 h-4 text-gray-700 mr-1" />
          <div class="text-gray-800 text-base">{{ item.label }}</div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script>
import { Badge, Popover, FeatherIcon } from "frappe-ui";

export default {
  name: "Tag",

  components: {
    Popover,
    Badge,
    FeatherIcon,
  },

  props: {
    entity: {
      type: Object,
      required: true,
      default: null,
    },
    tag: {
      type: Object,
      required: true,
      default: null,
    },
  },

  emits: ["success"],

  data() {
    return {
      colors: ["gray", "blue", "green", "orange", "red"],
      tagActions: [
        {
          label: "Delete",
          icon: "trash-2",
          handler: () => {
            this.$resources.deleteTag.submit();
          },
        },
      ],
    };
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
          entity: this.entity.name,
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
