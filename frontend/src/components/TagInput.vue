<template>
  <div class="min-w-full">
    <Popover>
      <template #target="{ isOpen, open: openPopover, togglePopover }">
        <slot
          name="target"
          v-bind="{ open: openPopover, togglePopover }"
        >
          <div
            class="flex items-center justify-start min-w-full flex-wrap gap-2"
          >
            <Tag
              v-for="tag in entityTags.data"
              :key="tag.name"
              :allow-delete="isOpen"
              :tag="tag"
              :entity="entity"
              @click="filterByTag(tag)"
              @success="entityTags.fetch()"
            />
            <span
              v-if="!entityTags.data?.length"
              class="text-ink-gray-7 text-base"
            >
              This file has no tags
            </span>
            <Button
              class="ml-auto"
              @click="togglePopover()"
            >
              Manage
            </Button>
          </div>
        </slot>
      </template>
      <template #body="{ isOpen, togglePopover }">
        <div
          v-if="isOpen"
          class="relative mt-1 rounded-lg bg-surface-white text-base shadow-2xl min-h-auto"
        >
          <div class="px-1.5 pb-1.5">
            <Input
              v-model="tagInputText"
              v-focus
              v-on-outside-click="closeInput"
              class="bg-surface-white py-1.5"
              placeholder="Search"
              type="text"
              @input="tagInputText = $event"
              @keydown.enter="
                (e) =>
                  createTag.submit({
                    title: tagInputText.trim(),
                    color: getRandomColor(),
                  })
              "
            />
            <ul
              v-if="filteredTags?.length"
              class="flex flex-col items-start justify-start max-h-[8rem] overflow-y-auto"
            >
              <li
                v-for="item in filteredTags"
                :key="item"
                class="flex items-center justify-start px-1.5 py-1 hover:bg-surface-gray-2 w-full rounded cursor-pointer"
                @click="
                  addTag.submit({
                    entity: entity.name,
                    tag: item.name,
                  })
                "
              >
                <div
                  class="flex items-center-justify-start rounded-[7px] px-1.5 py-1 gap-1"
                  :class="`bg-${item.color}-500 bg-opacity-10`"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <circle
                      r="4.5"
                      cx="8"
                      cy="8"
                      :fill="item.color"
                      :stroke="item.color"
                      stroke-width="3"
                    />
                  </svg>
                  <span
                    class="text-base"
                    :class="`text-${item.color}-700`"
                  >
                    {{ item.title }}
                  </span>
                </div>
              </li>
            </ul>
            <span
              v-else
              class="rounded-md px-2.5 py-1.5 text-base text-ink-gray-5"
              >No tags found</span
            >
          </div>
          <div class="flex items-center justify-end border-t p-1">
            <Button
              v-if="tagInputText"
              class="mr-auto px-2 py-1.5 hover:bg-surface-gray-2 rounded cursor-pointer"
              @click="
                (e) =>
                  createTag.submit({
                    title: tagInputText.trim(),
                    color: getRandomColor(),
                  })
              "
            >
              Create tag "{{ tagInputText }}"
            </Button>
            <Button
              class="px-2 py-1.5 hover:bg-surface-gray-2 rounded cursor-pointer"
              @click="removeTag.submit()"
            >
              Clear all
            </Button>
          </div>
        </div>
      </template>
    </Popover>
  </div>
</template>

<script setup>
import { getRandomColor } from "@/utils/random-color"
import { createResource, Input, Popover } from "frappe-ui"
import { ref, computed } from "vue"
import Tag from "./Tag.vue"
import { useStore } from "vuex"
import { useRoute } from "vue-router"

const store = useStore()
const route = useRoute()

const props = defineProps({ entity: Object })
const emit = defineEmits(["success", "close"])
const showTagInput = ref(false)
const tagInputText = ref("")
const hackyFlag = ref(false)

const unaddedTags = computed(() => {
  return userTags?.data?.filter(
    ({ name: id1 }) => !entityTags.data?.some?.(({ name: id2 }) => id2 === id1)
  )
})

const filteredTags = computed(() => {
  return unaddedTags.value.filter((x) =>
    x.title.toLowerCase().startsWith(tagInputText.value.toLowerCase())
  )
})

const closeInput = () => {
  if (hackyFlag.value) emit("close")
  hackyFlag.value = !hackyFlag.value
}

const filterByTag = (tag) => {
  if (route.name === "File" || route.name === "Document") return
  store.state.activeTags.push(tag)
}
const userTags = createResource({
  url: "drive.api.tags.get_user_tags",
  auto: true,
})

const entityTags = createResource({
  url: "drive.api.tags.get_entity_tags",
  makeParams: () => {
    return { entity: props.entity.name }
  },
  auto: true,
})

const createTag = createResource({
  url: "drive.api.tags.create_tag",
  onSuccess(data) {
    addTag.submit({
      entity: props.entity.name,
      tag: data,
    })
  },
})

const removeTag = createResource({
  url: "drive.api.tags.remove_tag",
  makeParams: () => ({
    entity: props.entity.name,
    all: true,
  }),
  onSuccess() {
    entityTags.fetch()
    emit("success")
  },
})

const addTag = createResource({
  url: "drive.api.tags.add_tag",
  onSuccess() {
    emit("success")
    entityTags.fetch()
    userTags.fetch()
  },
})
</script>
