<template>
  <div class="w-full">
    <Popover>
      <template #target="{ open: openPopover, togglePopover }">
        <slot name="target" v-bind="{ open: openPopover, togglePopover }">
          <div
            v-on-outside-click="closePopover()"
            class="flex items-center justify-start w-full flex-wrap gap-y-4 gap-x-2"
          >
            <Tag
              v-for="tag in $resources.entityTags.data"
              :key="tag.name"
              :tag="tag"
              :entity="entity"
            >
            </Tag>
            <span
              v-if="!$resources.entityTags.data?.length"
              class="text-gray-700 text-base"
            >
              This file has no tags
            </span>
            <Button class="ml-auto" @click="togglePopover()">Add Tag</Button>
          </div>
        </slot>
      </template>
      <template #body="{ isOpen, togglePopover }">
        <div
          v-show="isOpen"
          class="relative mt-1 rounded-lg bg-white text-base shadow-2xl min-h-auto"
        >
          <div class="px-1.5 pb-1.5">
            <Input
              class="bg-white py-1.5"
              placeholder="Search"
              v-model="tagInputText"
              v-focus
              v-on-outside-click="closeInput"
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
                    class="ml-auto"
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
              class="rounded-md px-2.5 py-1.5 text-base text-gray-600"
              v-else
              >No tags found</span
            >
          </div>
          <div class="flex items-center justify-end border-t p-1">
            <Button
              @click="
                (e) =>
                  $resources.createTag.submit({
                    title: tagInputText.trim(),
                    color: randomColor(),
                  })
              "
              v-if="tagInputText"
              class="mr-auto px-2 py-1.5 hover:bg-gray-100 rounded cursor-pointer"
            >
              Create tag "{{ tagInputText }}"
            </Button>
            <Button
              @click="$resources.removeTag.submit()"
              class="px-2 py-1.5 hover:bg-gray-100 rounded cursor-pointer"
            >
              Clear all
            </Button>
          </div>
        </div>
      </template>
    </Popover>
  </div>
</template>
<!--  <Popover transition="default" :show="hackyFlag && filteredTags.length">
      <template #target>
        <Input
          v-model="tagInputText"
          v-focus
          v-on-outside-click="closeInput"
          type="text"
          class="w-full"
          @input="tagInputText = $event"
          @keydown.enter="
            (e) =>
              $resources.createTag.submit({
                title: e.target.value.trim(),
              })
          "
        />
      </template>

      <template #body-main>
        <div class="p-1" @click.stop>
          <div v-for="tag in filteredTags" :key="tag.name">
            <div
              :class="`hover:bg-gray-100 cursor-pointer rounded-md py-1.5 px-2 text-gray-800 text-base`"
              @click="
                $resources.addTag.submit({
                  entity: entity.name,
                  tag: tag.name,
                })
              "
            >
              {{ tag.title }}
            </div>
          </div>
        </div>
      </template>
    </Popover> -->

<!-- <div class="flex items-center justify-start flex-wrap gap-y-4">
      <div
        v-if="$resources.entityTags.data?.length"
        class="flex flex-wrap gap-2 max-w-full"
      >
        <Tag
          v-for="tag in $resources.entityTags?.data"
          :key="tag"
          :tag="tag"
          :entity="entity"
          @success="
            () => {
              $resources.userTags.fetch()
              $resources.entityTags.fetch()
            }
          "
        />
      </div>
      <span v-else-if="!showTagInput" class="text-gray-700 text-base">
        This file has no tags
      </span>
      <Button
        v-if="!showTagInput && entity.owner === 'You'"
        class="ml-auto"
        @click="showTagInput = true"
      >
        Add tag
      </Button>
      <Input
        v-if="showTagInput"
        :entity="entity"
        :unadded-tags="unaddedTags"
        @success="
          () => {
            $resources.userTags.fetch()
            $resources.entityTags.fetch()
            showTagInput = false
          }
        "
        @close="showTagInput = false"
      />
    </div> -->
<script>
import { getRandomColor } from "@/utils/random-color"
import { Input, Popover, FeatherIcon } from "frappe-ui"
import Tag from "./Tag.vue"

export default {
  name: "TagInput",
  components: {
    Input,
    Popover,
    FeatherIcon,
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
