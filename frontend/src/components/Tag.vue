<template>
  <div
    class="inline-flex gap-1 items-center justify-center text-gray-800 border hover:bg-gray-200 h-7 text-base px-2 rounded group"
  >
    <button
      v-if="entity.owner === 'You'"
      class="hidden group-hover:block"
      icon="x"
      @click="$resources.removeTag.submit()"
    >
      <FeatherIcon
        class="my-auto h-4 w-4 stroke-2"
        name="x"
        @click="$resources.removeTag.submit()"
      />
    </button>
    <svg
      :class="entity.owner === 'You' ? 'block group-hover:hidden' : 'block'"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="8"
        cy="8"
        r="4.5"
        fill="transparent"
        :stroke="tag.color"
        stroke-width="3"
      />
    </svg>

    <span class="text-base text-gray-800">
      {{ tag.title }}
    </span>
  </div>
</template>

<!--  <Popover transition="default">
    <template #target="{ togglePopover }">
      <Badge
        class="text-base font-medium px-2"
        variant="subtle"
        :theme="`${tag.color}`"
        :style="{
          cursor: entity.owner === 'You' ? 'pointer' : 'default',
        }"
        @click="
          if (entity.owner === 'You');
          togglePopover()
        "
      >
        <span class="text-sm">{{ `${tag.title}` }}</span>
        <FeatherIcon
          v-if="entity.owner === 'You'"
          class="my-auto h-3 stroke-2"
          name="x"
          @click="$resources.removeTag.submit()"
        />
      </Badge>
    </template>
    <template #body-main="{ togglePopover }">
      <div class="bg-white rounded shadow-md p-1 z-10 space-y-0.5 absolute">
        <Popover
          placement="right"
          trigger="hover"
          :hover-delay="0.5"
          :leave-delay="0.6"
        >
          <template #target>
            <div
              class="hover:bg-gray-100 cursor-pointer rounded flex items-center px-1.5 py-1 w-24"
            >
              <FeatherIcon name="droplet" class="w-4 h-4 text-gray-700 mr-1" />
              <div class="text-gray-800 text-base">Color</div>
              <FeatherIcon
                name="chevron-right"
                class="w-4 h-4 text-gray-700 ml-auto"
              />
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
                  }),
                    toggleColors()
                "
              />
            </div>
          </template>
        </Popover>
        <div
          v-for="item in tagActions"
          :key="item"
          class="hover:bg-gray-100 cursor-pointer rounded flex items-center px-1.5 py-1 w-24"
          @click="item.handler(), togglePopover()"
        >
          <FeatherIcon :name="item.icon" class="w-4 h-4 text-gray-700 mr-1" />
          <div class="text-gray-800 text-base">{{ item.label }}</div>
        </div>
      </div>
    </template>
  </Popover> -->

<script>
import { Badge, Popover, FeatherIcon } from "frappe-ui"

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
            this.$resources.deleteTag.submit()
          },
        },
      ],
    }
  },

  resources: {
    updateColor() {
      return {
        url: "drive.api.tags.update_tag_color",
        onSuccess() {
          this.$emit("success")
        },
      }
    },

    removeTag() {
      return {
        url: "drive.api.tags.remove_tag",
        params: {
          entity: this.entity.name,
          tag: this.tag.name,
        },
        onSuccess() {
          this.$emit("success")
        },
      }
    },

    deleteTag() {
      return {
        url: "drive.api.tags.delete_tag",
        params: {
          tag: this.tag.name,
        },
        onSuccess() {
          this.$emit("success")
        },
      }
    },
  },
}
</script>
