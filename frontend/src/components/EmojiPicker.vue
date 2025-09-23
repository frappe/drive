<template>
  <Popover transition="default">
    <template #target="{ togglePopover, isOpen }">
      <slot v-bind="{ isOpen, togglePopover }">
        <Button
          v-if="emojiValue"
          variant="subtle"
          :title="emoji.value"
          :icon="emoji.icon"
          @click="togglePopover"
        />
        <span
          v-else
          @click="togglePopover"
          >Select</span
        >
      </slot>
    </template>
    <template #body="{ togglePopover }">
      <div class="bg-surface-white my-3 transform rounded px-4 sm:px-0">
        <div
          class="relative rounded shadow-2xl ring-1 ring-black ring-opacity-5"
        >
          <div class="flex gap-2 px-3 pb-1 pt-3">
            <div class="flex-1">
              <FormControl
                v-model="search"
                :placeholder="__('Search')"
              />
            </div>
            <Button
              variant="outline"
              :tooltip="Random"
              :icon="LucideDices"
              @click="
                () => {
                  setRandom()
                  togglePopover()
                }
              "
            />
          </div>
          <div class="max-h-64 overflow-y-auto">
            <div
              v-for="(emojis, group) in emojiGroups"
              :key="group"
              class="px-3"
            >
              <div
                v-if="group === 'No results'"
                class="bg-surface-white text-ink-gray-6 text-center text-sm py-4"
              >
                {{ group }}
              </div>
              <div
                v-else-if="group !== 'All'"
                class="bg-surface-white text-ink-gray-6 sticky top-0 py text-sm"
              >
                {{ group }}
              </div>
              <div
                v-if="emojis.length"
                class="grid grid-cols-10 place-items-center py-2"
              >
                <Button
                  v-for="_emoji in emojis"
                  variant="ghost"
                  class="hover:bg-surface-gray-2 h-8 w-8 rounded-md p-1 text-2xl"
                  :title="_emoji.value"
                  :icon="_emoji.icon"
                  @click="() => (emojiValue = _emoji.value) && togglePopover()"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import { computed, ref } from "vue"
import { Button, FormControl, Popover } from "frappe-ui"
import LucideDices from "~icons/lucide/dices"

const search = ref("")
const emojiValue = defineModel()

const props = defineProps({ emojis: Array })
const emoji = computed(() =>
  props.emojis.find((k) => k.value === emojiValue.value)
)

const emojiGroups = computed(() => {
  const groups = {}
  for (const _emoji of props.emojis) {
    if (search.value) {
      const searchTerm = _emoji.label + " " + _emoji.value
      if (!searchTerm.toLowerCase().includes(search.value.toLowerCase())) {
        continue
      }
    }

    let group = groups[_emoji.category || "All"]
    if (!group) {
      groups[_emoji.category || "All"] = []
      group = groups[_emoji.category || "All"]
    }
    group.push(_emoji)
  }
  if (!Object.keys(groups).length) {
    groups["No results"] = []
  }
  return groups
})

function setRandom() {
  const total = props.emojis.length
  const index = randomInt(0, total - 1)
  emojiValue.value = props.emojis[index].value
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min)
}

defineExpose({ setRandom })
</script>
