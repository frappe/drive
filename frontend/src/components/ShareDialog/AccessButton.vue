<template>
  <Popover v-slot="{ open, close }">
    <Float
      placement="bottom"
      :offset="2"
      portal
      as="div"
      class="relative w-full"
    >
      <PopoverButton
        class="flex gap-1 px-2 focus:outline-none bg-gray-100 rounded h-7 items-center text-base"
      >
        {{ accessObj.write ? "Can Edit" : "Can View" }}
        <span class="hidden">{{
          open ? disableScroll.on() : disableScroll.off()
        }}</span>

        <ChevronDown
          :class="{ '[transform:rotateX(180deg)]': open }"
          class="w-4"
        />
      </PopoverButton>
      <PopoverPanel class="z-10 bg-white p-1 shadow-2xl rounded w-full">
        <div v-if="open">
          <ul>
            <li
              class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
              @click="
                ;(accessObj.read = 1),
                  (accessObj.write = 0),
                  $emit('updateAccess'),
                  close()
              "
            >
              Can View
              <Check
                v-if="accessObj.read === 1 && accessObj.write === 0"
                class="h-3"
              />
            </li>
            <li
              class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
              @click="
                ;(accessObj.read = 1),
                  (accessObj.write = 1),
                  $emit('updateAccess'),
                  close()
              "
            >
              Can Edit
              <Check v-if="accessObj.write === 1" class="h-3" />
            </li>
            <hr class="my-0.5" />
            <li
              class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-1 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer text-red-500"
              @click="$emit('removeAccess'), close()"
            >
              Remove
            </li>
          </ul>
        </div>
      </PopoverPanel>
    </Float>
  </Popover>
</template>
<script setup>
import { ref } from "vue"
import { Float } from "@headlessui-float/vue"
import ChevronDown from "@/components/EspressoIcons/ChevronDown.vue"
import Check from "@/components/EspressoIcons/Check.vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import disableScroll from "../../utils/disable-scroll"

const props = defineProps(["accessObj"])
const accessObj = ref(props.accessObj)
defineEmits(["updateAccess", "removeAccess"])
</script>
