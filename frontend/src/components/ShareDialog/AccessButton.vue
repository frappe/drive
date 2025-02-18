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
        Manage
        <span class="hidden">{{
          open ? disableScroll.on() : disableScroll.off()
        }}</span>

        <ChevronDown
          :class="{ '[transform:rotateX(180deg)]': open }"
          class="w-3.5"
        />
      </PopoverButton>
      <PopoverPanel class="z-10 bg-white p-1 shadow-2xl rounded w-full">
        <div v-if="open">
          <ul>
            <li
              v-for="access in accessLevels"
              class="flex items-center justify-between px-1 text-base text-gray-700 line-clamp-1 py-1 gap-x-0.5 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer"
              @click="
                ;(accessObj[access] = !accessObj[access]),
                  $emit('updateAccess', { [access]: accessObj[access] }),
                  close()
              "
            >
              Can {{ access }}
              <Check v-if="accessObj[access]" class="h-3" />
            </li>
            <li
              v-if="accessLevels.find((k) => k === 'write')"
              class="flex items-center justify-between px-1 text-base line-clamp-1 py-1 gap-x-0.5 hover:bg-gray-100 w-full rounded-[6px] cursor-pointer text-red-500"
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
import { Float } from "@headlessui-float/vue"
import ChevronDown from "@/components/EspressoIcons/ChevronDown.vue"
import Check from "@/components/EspressoIcons/Check.vue"
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/vue"
import disableScroll from "../../utils/disable-scroll"
import { ref } from "vue"

const props = defineProps({ accessLevels: Object, accessObj: Object })
const accessObj = ref(props.accessObj)
console.log(props.accessLevels)
defineEmits(["updateAccess", "removeAccess"])
</script>
