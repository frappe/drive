<script setup lang="ts">
import { Editor, Node, NodeViewWrapper } from "@tiptap/vue-3"
import { ref, onMounted, computed, watch } from "vue"
import { Node as ProseMirrorNode } from "prosemirror-model"
import { Decoration } from "prosemirror-view"
import { resizableMediaActions } from "../extensions/resizenode/resizableMediaMenuUtil"
import "tippy.js/animations/shift-away.css"
import AlignItemLeft from "../icons/align-item-left.vue"
import AlignItemRight from "../icons/align-item-right.vue"
import AlignItemCenter from "../icons/align-item-center.vue"
import FloatItemLeft from "../icons/float-item-left.vue"
import FloatItemRight from "../icons/float-item-right.vue"

interface Props {
  editor: Editor
  node: ProseMirrorNode
  decorations: Decoration
  selected: boolean
  extension: Node<any, any>
  getPos: () => number
  updateAttributes: (attributes: Record<string, any>) => void
  deleteNode: () => void
}

const props = defineProps<Props>()

const mediaType = computed<"img" | "video">(
  () => props.node.attrs["media-type"]
)

const resizableImg = ref<HTMLImageElement | HTMLVideoElement | null>(null) // template ref

const aspectRatio = ref(0)

const proseMirrorContainerWidth = ref(0)

const mediaActionActiveState = ref<Record<string, boolean>>({})

const showActionMenu = ref(true)

const setMediaActionActiveStates = () => {
  const activeStates: Record<string, boolean> = {}

  for (const { tooltip, isActive } of resizableMediaActions)
    activeStates[tooltip] = !!isActive?.(props.node.attrs)

  mediaActionActiveState.value = activeStates
}

watch(
  () => props.node.attrs,
  () => setMediaActionActiveStates(),
  { deep: true }
)

const mediaSetupOnLoad = () => {
  // ! TODO: move this to extension storage
  const proseMirrorContainerDiv = document.querySelector(".ProseMirror")

  if (proseMirrorContainerDiv)
    proseMirrorContainerWidth.value = proseMirrorContainerDiv?.clientWidth

  // When the media has loaded
  if (!resizableImg.value) return
  aspectRatio.value =
    (resizableImg.value as HTMLVideoElement).videoWidth /
    (resizableImg.value as HTMLVideoElement).videoHeight
}

onMounted(() => mediaSetupOnLoad())

const isHorizontalResizeActive = ref(false)
const activeDragHandle = ref("left")
const lastCursorX = ref(-1)

interface WidthAndHeight {
  width: number
  height: number
}

const limitWidthOrHeightToFiftyPixels = ({ width, height }: WidthAndHeight) =>
  width < 250 || height < 250

const startHorizontalResize = (e: MouseEvent, dragHandle: string) => {
  activeDragHandle.value = dragHandle
  isHorizontalResizeActive.value = true
  lastCursorX.value = e.clientX

  document.addEventListener("mousemove", onHorizontalMouseMove)
  document.addEventListener("mouseup", stopHorizontalResize)
}

const stopHorizontalResize = () => {
  isHorizontalResizeActive.value = false
  lastCursorX.value = -1
  showActionMenu.value = false

  document.removeEventListener("mousemove", onHorizontalMouseMove)
  document.removeEventListener("mouseup", stopHorizontalResize)
}

const onHorizontalResize = (
  directionOfMouseMove: "right" | "left",
  diff: number
) => {
  if (!resizableImg.value) {
    console.error("Media ref is undefined|null", {
      resizableImg: resizableImg.value,
    })
    return
  }

  const currentMediaDimensions = {
    width: resizableImg.value?.width,
    height: resizableImg.value?.height,
  }

  const newMediaDimensions = {
    width: -1,
    height: -1,
  }

  if (directionOfMouseMove === "left") {
    newMediaDimensions.width = currentMediaDimensions.width - Math.abs(diff)
  } else {
    newMediaDimensions.width = currentMediaDimensions.width + Math.abs(diff)
  }

  //if (newMediaDimensions.width > proseMirrorContainerWidth.value)
  //  newMediaDimensions.width = proseMirrorContainerWidth.value;

  newMediaDimensions.height = newMediaDimensions.width / aspectRatio.value

  if (limitWidthOrHeightToFiftyPixels(newMediaDimensions)) return
  props.updateAttributes(newMediaDimensions)
}

const onHorizontalMouseMove = (e: MouseEvent) => {
  if (!isHorizontalResizeActive.value) return

  const { clientX } = e

  const diff = lastCursorX.value - clientX

  lastCursorX.value = clientX

  if (diff === 0) return

  let directionOfMouseMove: "left" | "right"
  if (activeDragHandle.value === "left") {
    directionOfMouseMove = diff > 0 ? "right" : "left"
  } else if (activeDragHandle.value === "right") {
    directionOfMouseMove = diff > 0 ? "left" : "right"
  }

  onHorizontalResize(directionOfMouseMove, Math.abs(diff))
}

const lastCursorY = ref(-1)

const floatClass = computed(() => {
  switch (props.node.attrs.dataFloat) {
    case "left":
      return "float-left mr-4"
    case "right":
      return "float-right ml-4"
    default:
      return ""
  }
})

const alignClass = computed(() => {
  switch (props.node.attrs.dataAlign) {
    case "left":
      return "justify-start"
    case "center":
      return "justify-center"
    case "right":
      return "justify-end"
    default:
      return "justify-end"
  }
})
</script>

<template>
  <node-view-wrapper
    as="div"
    class="group relative flex not-prose"
    :class="props.node.attrs.dataAlign ? alignClass : floatClass"
  >
    <div
      class="relative flex items-center group"
      v-if="props.editor.options.editable"
      draggable="true"
      data-drag-handle
    >
      <div
        class="transition-opacity duration-100 ease-in-out opacity-0 group-hover:opacity-100 absolute -top-10 right-0 bg-surface-white border flex items-center justify-center shadow-lg rounded-[0.55rem] gap-x-1 p-0.5"
      >
        <button
          class="rounded p-1"
          :class="
            props.node.attrs.dataAlign === 'left'
              ? 'bg-surface-gray-3 text-ink-gray-5'
              : ''
          "
          :variant="'ghost'"
          @click="
            props.updateAttributes({
              dataAlign: 'left',
              dataFloat: null,
            })
          "
        >
          <AlignItemLeft class="rounded-none w-4 h-auto" />
        </button>
        <button
          class="rounded p-1"
          :class="
            props.node.attrs.dataAlign === 'center'
              ? 'bg-surface-gray-3 text-ink-gray-5'
              : ''
          "
          :variant="'ghost'"
          @click="
            props.updateAttributes({
              dataAlign: 'center',
              dataFloat: null,
            })
          "
        >
          <AlignItemCenter class="rounded-none w-4 h-auto" />
        </button>
        <button
          class="rounded p-1"
          :class="
            props.node.attrs.dataAlign === 'right'
              ? 'bg-surface-gray-3 text-ink-gray-5'
              : ''
          "
          :variant="'ghost'"
          @click="
            props.updateAttributes({
              dataAlign: 'right',
              dataFloat: null,
            })
          "
        >
          <AlignItemRight class="w-4 h-auto" />
        </button>
        <button
          class="rounded p-1"
          :class="
            props.node.attrs.dataFloat === 'left'
              ? 'bg-surface-gray-3 text-ink-gray-5'
              : ''
          "
          :variant="'ghost'"
          @click="
            props.updateAttributes({
              dataAlign: null,
              dataFloat: 'left',
            })
          "
        >
          <FloatItemLeft class="w-4 h-auto" />
        </button>
        <button
          class="rounded p-1"
          :class="
            props.node.attrs.dataFloat === 'right'
              ? 'bg-surface-gray-3 text-ink-gray-5'
              : ''
          "
          :variant="'ghost'"
          @click="
            props.updateAttributes({
              dataAlign: null,
              dataFloat: 'right',
            })
          "
        >
          <FloatItemRight class="w-4 h-auto" />
        </button>
      </div>
      <!-- Left Handle -->
      <div
        class="z-10 absolute left-0 flex items-center justify-center w-5 h-full bg-transparent cursor-ew-resize"
        @mousedown.lazy.prevent="startHorizontalResize($event, 'left')"
        @mouseup.lazy.prevent="stopHorizontalResize"
      >
        <div
          class="transition-opacity duration-100 ease-in-out opacity-0 group-hover:opacity-100 absolute w-2 bg-surface-white bg-opacity-80 rounded h-[55px] shadow-xl"
        />
      </div>
      <img
        v-if="mediaType === 'img'"
        v-bind="node.attrs"
        loading="lazy"
        ref="resizableImg"
        class="rounded"
        draggable="false"
      />

      <video
        v-else-if="mediaType === 'video'"
        v-bind="node.attrs"
        loading="lazy"
        ref="resizableImg"
        class="rounded"
        controls="true"
        draggable="false"
        controlslist="nodownload noremoteplayback noplaybackrate disablepictureinpicture"
      >
        <source :src="node.attrs.src" />
      </video>
      <!-- Right Handle -->
      <div
        class="absolute z-10 right-0 flex items-center justify-center w-5 h-full bg-transparent cursor-ew-resize"
        @mousedown.lazy.prevent="startHorizontalResize($event, 'right')"
        @mouseup.lazy.prevent="stopHorizontalResize"
      >
        <div
          class="absolute w-2 bg-surface-white bg-opacity-80 rounded h-[55px] transition-opacity duration-100 ease-in-out opacity-0 group-hover:opacity-100 shadow-xl"
        />
      </div>
    </div>

    <div
      v-else
      class="w-fit flex relative"
    >
      <img
        v-if="mediaType === 'img'"
        loading="lazy"
        v-bind="node.attrs"
        ref="resizableImg"
        class="rounded"
        draggable="false"
      />

      <video
        v-else-if="mediaType === 'video'"
        loading="lazy"
        v-bind="node.attrs"
        ref="resizableImg"
        class="rounded"
        draggable="false"
        controls="true"
        controlslist="nodownload noremoteplayback noplaybackrate disablepictureinpicture"
      >
        <source :src="node.attrs.src" />
      </video>
    </div>
  </node-view-wrapper>
</template>
