<template>
  <div
    class="flex items-center justify-center bg-white w-full shadow-lg rounded-[0.45rem] gap-1 px-0.5 py-0.5"
  >
    <template v-for="button in buttons" :key="button.label">
      <div v-if="button.type === 'separator'" class="h-5 border-l"></div>
      <div v-else-if="button.map" class="shrink-0">
        <Popover>
          <template #target="{ togglePopover }">
            <button
              class="rounded text-base font-medium text-gray-800 transition-colors hover:bg-gray-100"
              :set="
                (activeBtn =
                  button.find((b) => b.isActive(editor)) || button[0])
              "
              @click="togglePopover"
            >
              <component
                :is="activeBtn.icon"
                v-if="activeBtn.icon"
                class="h-4 w-4"
              />
              <span v-else>
                {{ activeBtn.label }}
              </span>
            </button>
          </template>
          <template #body="{ close }">
            <ul class="rounded border bg-white p-1 shadow-md">
              <li
                v-for="option in button"
                v-show="option.isDisabled ? !option.isDisabled(editor) : true"
                :key="option.label"
                class="w-full"
              >
                <button
                  class="w-full rounded px-2 py-1 text-left text-base hover:bg-gray-50"
                  @click="
                    () => {
                      onButtonClick(option)
                      close()
                    }
                  "
                >
                  {{ option.label }}
                </button>
              </li>
            </ul>
          </template>
        </Popover>
      </div>
      <component :is="button.component || 'div'" v-else v-bind="{ editor }">
        <template #default="componentSlotProps">
          <button
            class="flex items-center rounded-[0.35rem] p-1 text-gray-800 transition-colors gap-1"
            :class="
              button.isActive(editor) || componentSlotProps?.isActive
                ? 'bg-gray-200 text-gray-400'
                : 'hover:bg-gray-100'
            "
            :title="button.label"
            @click="
              componentSlotProps?.onClick
                ? componentSlotProps.onClick(button)
                : onButtonClick(button)
            "
          >
            <component
              :is="button.icon"
              v-if="button.icon"
              class="h-4 w-auto stroke-[1.5]"
            />
            <span
              v-else
              class="inline-block h-4 min-w-[1rem] text-sm leading-4"
            >
              {{ button.text }}
            </span>
          </button>
        </template>
      </component>
    </template>
  </div>
</template>
<script>
import { Popover, FeatherIcon } from "frappe-ui"

export default {
  name: "TipTapMenu",
  components: {
    Popover,
    FeatherIcon,
  },
  inject: ["editor"],
  props: ["buttons"],
  emits: ["toggleCommentMode"],

  methods: {
    onButtonClick(button) {
      if (typeof button.action === "string") {
        this.emitter.emit(button.action)
      } else {
        button.action(this.editor)
      }
    },
  },
}
</script>
