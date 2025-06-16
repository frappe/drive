<template>
  <div
    v-if="activity.document_field.startsWith('User')"
    class="border max-w-[220px] rounded-[7px] px-1 py-1 gap-x-1 flex items-center justify-center overflow-clip text-sm"
    :class="
      activity.action_type === 'share_remove'
        ? 'strike-div text-ink-gray-4'
        : 'text-ink-gray-7'
    "
  >
    <Avatar
      size="xs"
      :image="activity.share_user_image"
      :label="
        activity.share_user_fullname
          ? activity.share_user_fullname
          : activity.new_value
      "
    />
    <span class="flex gap-x-0.5 items-center justify-start">
      <span class="line-clamp-1">{{
        activity.share_user_fullname
          ? activity.share_user_fullname
          : activity.new_value
      }}</span>
      <span>∙</span>
      <span class="text-ink-gray-5">
        {{
          activity.meta_value === "1"
            ? "View"
            : activity.meta_value === "2"
            ? "Edit"
            : "Share"
        }}</span
      >
    </span>
  </div>
  <div
    v-else
    class="border max-w-[220px] rounded-[7px] px-1 py-1 gap-x-1 flex items-center justify-center overflow-clip text-sm"
    :class="
      activity.action_type === 'share_remove'
        ? 'strike-div text-ink-gray-3'
        : 'text-ink-gray-8'
    "
  >
    <GeneralAccess
      size="sm"
      :disabled="activity.action_type === 'share_remove' ? true : false"
      :general-access="{
        [activity.document_field]: activity.new_value,
      }"
    />
    <span class="flex gap-x-0.5 items-center justify-start">
      <span>{{
        activity.document_field === "everyone" ? "Organization" : "Public"
      }}</span>
      <span>∙</span>
      <span class="text-ink-gray-5">{{
        activity.meta_value === "1"
          ? "View"
          : activity.meta_value === "2"
          ? "Edit"
          : "Full Access"
      }}</span>
    </span>
  </div>
  <slot name="nested" />
</template>
<script setup>
import { Avatar } from "frappe-ui"
import GeneralAccess from "./GeneralAccess.vue"

const props = defineProps({
  title: {
    type: String,
    default: "File",
    required: false,
  },
  activity: {
    type: Object,
    required: true,
  },
  strikeThrough: {
    type: Boolean,
    default: false,
    required: false,
  },
})
</script>

<style>
.strike-div {
  position: relative;
  font-size: 0px;
  text-align: center;
}

.strike-div::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  width: 96%;
  margin: auto;
  height: 1px;
  background-color: rgb(148, 148, 148);
}
.strike-div img {
  filter: grayscale(100%);
}
</style>
