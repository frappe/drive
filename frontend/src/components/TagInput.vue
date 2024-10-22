<template>
  <div class="min-w-full">
    <Popover>
      <template #target="{ isOpen, open: openPopover, togglePopover }">
        <slot name="target" v-bind="{ open: openPopover, togglePopover }">
          <div
            class="flex items-center justify-start min-w-full flex-wrap gap-2"
          >
            <Tag
              v-for="tag in $resources.entityTags.data"
              :key="tag.name"
              :allow-delete="isOpen"
              :tag="tag"
              :entity="entity"
              @click="filterByTag(tag)"
              @success="$resources.entityTags.fetch()"
            >
            </Tag>
            <span
              v-if="!$resources.entityTags.data?.length"
              class="text-gray-700 text-base"
            >
              This file has no tags
            </span>
            <Button class="ml-auto" @click="togglePopover()">Manage</Button>
          </div>
        </slot>
      </template>
      <template #body="{ isOpen, togglePopover }">
        <div
          v-if="isOpen"
          class="relative mt-1 rounded-lg bg-white text-base shadow-2xl min-h-auto"
        >
          <div class="px-1.5 pb-1.5">
            <Input
              v-model="tagInputText"
              v-focus
              v-on-outside-click="closeInput"
              class="bg-white py-1.5"
              placeholder="Search"
              type="text"
              @input="tagInputText = $event"
              @keydown.enter="
                (e) =>
                  $resources.createTag.submit({
                    title: tagInputText.trim(),
                    color: randomColor(),
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
                class="flex items-center justify-start px-1.5 py-1 hover:bg-gray-100 w-full rounded cursor-pointer"
                @click="
                  $resources.addTag.submit({
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
                  <span class="text-base" :class="`text-${item.color}-700`">
                    {{ item.title }}
                  </span>
                </div>
              </li>
            </ul>
            <span
              v-else
              class="rounded-md px-2.5 py-1.5 text-base text-gray-600"
              >No tags found</span
            >
          </div>
          <div class="flex items-center justify-end border-t p-1">
            <Button
              v-if="tagInputText"
              class="mr-auto px-2 py-1.5 hover:bg-gray-100 rounded cursor-pointer"
              @click="
                (e) =>
                  $resources.createTag.submit({
                    title: tagInputText.trim(),
                    color: randomColor(),
                  })
              "
            >
              Create tag "{{ tagInputText }}"
            </Button>
            <Button
              class="px-2 py-1.5 hover:bg-gray-100 rounded cursor-pointer"
              @click="$resources.removeTag.submit()"
            >
              Clear all
            </Button>
          </div>
        </div>
      </template>
    </Popover>
  </div>
</template>

<script>
import { getRandomColor } from "@/utils/random-color"
import { Input, Popover } from "frappe-ui"
import Tag from "./Tag.vue"
import { routeLocationKey } from "vue-router"

export default {
  name: "TagInput",
  components: {
    Input,
    Popover,
    Tag,
  },

  props: {
    entity: {
      type: Object,
      required: true,
      default: null,
    },
  },

  emits: ["success", "close"],
  expose: ["togglePopover"],
  data() {
    return {
      showTagInput: false,
      tagInputText: "",
      hackyFlag: false, // temporary hacky flag to circumvent v-on-outside-click from running on mounting
    }
  },

  computed: {
    unaddedTags() {
      return this.$resources.userTags?.data?.filter(
        ({ name: id1 }) =>
          !this.$resources.entityTags?.data?.some(
            ({ name: id2 }) => id2 === id1
          )
      )
    },

    filteredTags() {
      return this.unaddedTags?.filter((x) =>
        x.title.toLowerCase().startsWith(this.tagInputText.toLowerCase())
      )
    },
  },

  methods: {
    togglePopover(val) {
      this.showTagInput = val ?? !this.showTagInput
    },
    randomColor() {
      return getRandomColor()
    },
    closeInput() {
      if (this.hackyFlag) this.$emit("close")
      this.hackyFlag = !this.hackyFlag
    },
    filterByTag(tag) {
      if (this.$route.name === "File" || this.$route.name === "Document") return
      this.$store.state.activeTags.push(tag)
    },
  },

  resources: {
    userTags() {
      return {
        url: "drive.api.tags.get_user_tags",
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
        auto: true,
      }
    },
    entityTags() {
      return {
        url: "drive.api.tags.get_entity_tags",
        params: { entity: this.entity.name },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
        auto: true,
      }
    },
    createTag() {
      return {
        url: "drive.api.tags.create_tag",
        onSuccess(data) {
          this.$resources.addTag.submit({
            entity: this.entity.name,
            tag: data,
          })
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
      }
    },
    removeTag() {
      return {
        url: "drive.api.tags.remove_tag",
        params: {
          entity: this.entity.name,
          all: true,
        },
        onSuccess() {
          this.$resources.entityTags.fetch()
          this.$emit("success")
        },
      }
    },
    addTag() {
      return {
        url: "drive.api.tags.add_tag",
        onSuccess() {
          this.$emit("success")
          this.$resources.entityTags.fetch()
          this.$resources.userTags.fetch()
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
      }
    },
  },
}
</script>
