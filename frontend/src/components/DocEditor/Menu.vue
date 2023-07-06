<template>
  <div class="inline-flex bg-white px-4 py-1 w-full shadow-sm">
    <div class="inline-flex items-center gap-1">
      <template v-for="button in buttons" :key="button.label">
        <div
          v-if="button.type === 'separator'"
          class="h-4 w-[2px] border-l"></div>
        <div v-else-if="button.map" class="shrink-0">
          <Popover>
            <template #target="{ togglePopover }">
              <button
                class="rounded px-2 py-1 text-base font-medium text-gray-800 transition-colors hover:bg-gray-100"
                :set="
                  (activeBtn =
                    button.find((b) => b.isActive(editor)) || button[0])
                "
                @click="togglePopover">
                <component
                  :is="activeBtn.icon"
                  v-if="activeBtn.icon"
                  class="h-4 w-4" />
                <span v-else>
                  {{ activeBtn.label }}
                </span>
              </button>
            </template>
            <template #body="{ close }">
              <ul class="rounded border bg-white p-1 shadow-md">
                <li
                  v-show="option.isDisabled ? !option.isDisabled(editor) : true"
                  class="w-full"
                  v-for="option in button">
                  <button
                    class="w-full rounded px-2 py-1 text-left text-base hover:bg-gray-50"
                    @click="
                      () => {
                        onButtonClick(option);
                        close();
                      }
                    ">
                    {{ option.label }}
                  </button>
                </li>
              </ul>
            </template>
          </Popover>
        </div>
        <component v-else :is="button.component || 'div'" v-bind="{ editor }">
          <template v-slot="componentSlotProps">
            <button
              class="flex rounded p-1 text-gray-800 transition-colors"
              :class="
                button.isActive(editor) || componentSlotProps?.isActive
                  ? 'bg-gray-100'
                  : 'hover:bg-gray-100'
              "
              :title="button.label"
              @click="
                componentSlotProps?.onClick
                  ? componentSlotProps.onClick(button)
                  : onButtonClick(button)
              ">
              <component v-if="button.icon" :is="button.icon" class="h-4 w-4" />
              <span
                v-else
                class="inline-block h-4 min-w-[1rem] text-sm leading-4">
                {{ button.text }}
              </span>
            </button>
          </template>
        </component>
      </template>
    </div>
  </div>
</template>
<script>
import { Popover } from "frappe-ui";

export default {
  name: "TipTapMenu",
  props: ["buttons"],
  inject: ["editor"],
  emits: ["toggleCommentMode"],
  components: {
    Popover,
  },

  methods: {
    onButtonClick(button) {
      if (typeof button.action === "string") {
        this.emitter.emit(button.action);
      } else {
        button.action(this.editor);
      }
    },
  },
};
</script>
