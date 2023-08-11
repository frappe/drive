<template>
  <Transition
    enter-from-class="translate-x-[150%] opacity-0"
    leave-to-class="translate-x-[150%] opacity-0"
    enter-active-class="transition duration-125"
    leave-active-class="transition duration-125">
    <div
      v-if="showInfoSidebar"
      class="flex flex-col justify-start scroll-pb-44 min-w-[350px] max-w-[350px] min-h-full border-l z-0 overflow-y-auto">
      <div v-if="entity" class="w-full border-b p-4">
        <div class="flex items-center">
          <svg
            v-if="entity.is_group"
            :style="{ fill: entity.color }"
            :draggable="false"
            class="h-5 mr-2.5"
            viewBox="0 0 46 40"
            fill="#32a852"
            xmlns="http://www.w3.org/2000/svg">
            <path
              d="M0.368197 17.3301C0.17175 15.5535 1.56262 14.0004 3.35002 14.0004H42.65C44.4374 14.0004 45.8283 15.5535 45.6318 17.3301L43.7155 34.6599C43.3794 37.6999 40.8104 40.0004 37.7519 40.0004H8.24812C5.18961 40.0004 2.62062 37.6999 2.28447 34.6599L0.368197 17.3301Z" />
            <path
              d="M43.125 11V9C43.125 6.79086 41.3341 5 39.125 5H20.312C20.1914 5 20.0749 4.95643 19.9839 4.8773L14.6572 0.245394C14.4752 0.0871501 14.2422 0 14.001 0H6.87501C4.66587 0 2.87501 1.79086 2.87501 4V11C2.87501 11.5523 3.32272 12 3.87501 12H42.125C42.6773 12 43.125 11.5523 43.125 11Z" />
          </svg>
          <img
            v-else
            :src="getIconUrl(formatMimeType(entity.mime_type))"
            :draggable="false"
            class="h-5 mr-2.5" />
          <div class="font-medium truncate text-xl">
            {{ entity.title }}
          </div>
        </div>
      </div>
      <!-- :class="$store.state.showInfo ? 'min-h-[45px]' : 'min-h-[48px]'" -->
      <!-- grow  min-h-full -->
      <div v-if="entity">
        <div class="flex flex-col justify-start">
          <div
            v-if="tab === 0"
            class="p-4 border-b"
            :class="
              tab === 0
                ? 'flex-auto'
                : 'text-gray-600 cursor-pointer flex-none '
            "
            @click="tab = 0">
            <span class="font-medium text-lg">Doc Info</span>
            <div
              v-if="tab === 0"
              class="space-y-7 min-h-full flex-auto flex flex-col z-0 overflow-y-auto">
              <div v-if="entity.owner === 'me'">
                <div class="text-lg font-medium my-4">Manage Access</div>
                <div class="flex flex-row">
                  <Button class="h-7" @click="showShareDialog = true">
                    Share
                  </Button>
                </div>
              </div>
              <ShareDialog
                v-if="showShareDialog"
                v-model="showShareDialog"
                :entity-name="entity.name" />
              <div
                v-if="
                  entity.owner === 'me' || $resources.entityTags.data?.length
                ">
                <div class="text-lg font-medium mb-4">Tag</div>
                <div class="flex flex-wrap gap-2">
                  <Tag
                    v-for="tag in $resources.entityTags.data"
                    :key="tag"
                    :tag="tag"
                    :entity="entity"
                    @success="
                      () => {
                        $resources.userTags.fetch();
                        $resources.entityTags.fetch();
                      }
                    " />
                  <Button
                    v-if="!addTag && entity.owner === 'me'"
                    class="h-6 text-[12px] text-gray-800"
                    icon-left="plus"
                    @click="addTag = true">
                    Add tag
                  </Button>
                </div>

                <TagInput
                  v-if="addTag"
                  :class="{ 'mt-2': $resources.entityTags.data.length }"
                  :entity="entity"
                  :unadded-tags="unaddedTags"
                  @success="
                    () => {
                      $resources.userTags.fetch();
                      $resources.entityTags.fetch();
                      addTag = false;
                    }
                  "
                  @close="addTag = false" />
              </div>
              <div class="text-lg font-medium mb-4">Properties</div>
              <div class="flex text-base">
                <div class="w-1/2 text-gray-600 space-y-2">
                  <div>Type</div>
                  <div>Size</div>
                  <div>Modified</div>
                  <div>Created</div>
                  <div>Owner</div>
                </div>
                <div class="w-1/2 space-y-2">
                  <div>Frappe Doc</div>
                  <div>{{ entity.file_size }}</div>
                  <div>{{ entity.modified }}</div>
                  <div>{{ entity.creation }}</div>
                  <div>{{ entity.owner }}</div>
                </div>
              </div>
              <div class="text-gray-600 text-base">
                Viewers can download this file.
              </div>
            </div>
          </div>
          <div
            v-if="tab === 1"
            class="p-4 border-b"
            :class="tab === 1 ? 'flex-auto' : 'text-gray-600 cursor-pointer'"
            @click="tab = 1">
            <span class="font-medium text-lg">Comments</span>
            <div v-if="tab === 1" class="h-full overflow-y-auto">
              <div v-if="entity.allow_comments" class="space-y-5">
                <div
                  v-for="comment in $resources.comments.data"
                  :key="comment"
                  class="flex gap-3 my-4 items-center">
                  <Avatar
                    :label="comment.comment_by"
                    :image="comment.user_image"
                    class="h-7 w-7" />
                  <div>
                    <span class="my-1">
                      <span class="text-sm font-medium">
                        {{ comment.comment_by }}
                      </span>
                      <span class="text-gray-500 text-sm">{{ " ∙ " }}</span>
                      <span class="text-gray-700 text-sm">
                        {{ comment.creation }}
                      </span>
                    </span>
                    <div class="text-base text-gray-700">
                      {{ comment.content }}
                    </div>
                  </div>
                </div>
                <div v-if="userId != 'Guest'" class="flex items-center gap-3">
                  <Avatar :label="fullName" :image="imageURL" class="h-7 w-7" />
                  <div class="flex">
                    <Input
                      v-model="newComment"
                      type="text"
                      class="border-gray-400 placeholder-gray-500 w-full grow bg-white focus:bg-white"
                      placeholder="Add comment"
                      @keydown.enter="postComment" />
                  </div>
                  <Button @click="postComment" variant="solid">Add</Button>
                </div>
              </div>
              <OuterCommentVue
                v-if="!!allComments.length"
                :active-comments-instance="activeCommentsInstance"
                :all-comments="allComments"
                :focus-content="focusContent"
                @set-comment="setComment" />
              <div v-else class="text-gray-600 text-base mt-2">
                There are no comments for the current document
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-else
        class="flex h-full w-full flex-col items-center justify-center rounded-lg text-center">
        <svg viewBox="0 0 78 85" class="w-1/6 fill-transparent stroke-2 pb-6">
          <path
            d="M42 31H66 M42 51H66 M42 25H55 M42 45H55 M65 9V8C65 4.13401 61.866 1 58 1H8C4.13401 1 1 4.13401 1 8V66C1 69.866 4.13401 73 8 73H10 M70 12H20C16.134 12 13 15.134 13 19V77C13 80.866 16.134 84 20 84H70C73.866 84 77 80.866 77 77V19C77 15.134 73.866 12 70 12Z"
            stroke="#525252" />
          <path
            d="M32 43H26C24.8954 43 24 43.8954 24 45V51C24 52.1046 24.8954 53 26 53H32C33.1046 53 34 52.1046 34 51V45C34 43.8954 33.1046 43 32 43Z M32 23H26C24.8954 23 24 23.8954 24 25V31C24 32.1046 24.8954 33 26 33H32C33.1046 33 34 32.1046 34 31V25C34 23.8954 33.1046 23 32 23Z"
            stroke="#525252" />
        </svg>
        <p class="text-base font-medium">No file selected</p>
        <p class="text-sm text-gray-600">
          Select a file to get more information
        </p>
      </div>

      <div
        v-if="tab === 2"
        class="p-4 border-b space-y-2"
        :class="
          tab === 2 ? 'flex-auto' : 'text-gray-600 cursor-pointer flex-none '
        "
        @click="tab = 2">
        <span class="font-medium text-lg">Typography</span>
        <div class="space-y-2" v-if="tab === 2">
          <span class="font-medium text-gray-600 text-md">Presets</span>
          <div
            class="flex flex-row w-full bg-gray-100 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8">
            <Button
              class="w-full"
              :class="
                editor.isActive('heading', { level: 1 })
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="
                editor
                  .chain()
                  .focus()
                  .unsetFontSize()
                  .toggleHeading({ level: 1 })
                  .run()
              ">
              Title
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('heading', { level: 2 })
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="
                editor
                  .chain()
                  .focus()
                  .unsetMark('bold')
                  .unsetFontSize()
                  .toggleHeading({ level: 2 })
                  .run()
              ">
              Heading
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('heading', { level: 3 })
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="
                editor
                  .chain()
                  .focus()
                  .unsetMark('bold')
                  .unsetFontSize()
                  .toggleHeading({ level: 3 })
                  .run()
              ">
              Subtitle
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('paragraph')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="
                editor
                  .chain()
                  .focus()
                  .unsetMark('bold')
                  .unsetFontSize()
                  .setParagraph()
                  .run()
              ">
              Body
            </Button>
          </div>

          <Popover>
            <template #target="{ togglePopover }">
              <Button
                variant="minimal"
                class="flex-auto w-full border text-lg text-gray-800 transition-colors hover:bg-gray-100"
                :set="
                  (activeBtn =
                    fontFamilyOptions.find((f) => f.isActive(editor)) ||
                    fontFamilyOptions[0])
                "
                @click="togglePopover">
                <span>
                  {{ activeBtn.label }}
                </span>
              </Button>
            </template>
            <template #body="{ close }">
              <ul class="rounded bg-white p-2 shadow-sm border">
                <li
                  v-for="option in fontFamilyOptions"
                  v-show="option.isDisabled ? !option.isDisabled(editor) : true"
                  :key="option.label"
                  class="w-full">
                  <button
                    class="rounded text-left text-base hover:bg-gray-50"
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

          <Input />

          <Popover>
            <template #target="{ togglePopover }">
              <Button
                variant="minimal"
                class="border flex-auto w-1/3 text-lg text-gray-800 transition-colors hover:bg-gray-100"
                :set="
                  (activeBtn =
                    fontSizeOptions.find((f) => f.isActive(editor)) ||
                    fontSizeOptions[0])
                "
                @click="togglePopover">
                <span>
                  {{ activeBtn.label }}
                </span>
              </Button>
            </template>
            <template #body="{ close }">
              <ul class="rounded border bg-white p-1 shadow-sm">
                <li
                  v-for="option in fontSizeOptions"
                  v-show="option.isDisabled ? !option.isDisabled(editor) : true"
                  :key="option.label"
                  class="w-full">
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

          <Popover>
            <template #target="{ togglePopover }">
              <Button
                variant="minimal"
                class="flex-auto w-full border text-lg text-gray-800 transition-colors hover:bg-gray-100"
                :set="
                  (activeBtn =
                    lineOptions.find((f) => f.isActive(editor)) ||
                    lineOptions[0])
                "
                @click="togglePopover">
                <span>Line Height: {{ activeBtn.label }}</span>
              </Button>
            </template>
            <template #body="{ close }">
              <ul class="rounded border bg-white p-1 shadow-md">
                <li
                  v-for="option in lineOptions"
                  v-show="option.isDisabled ? !option.isDisabled(editor) : true"
                  :key="option.label"
                  class="w-full">
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

          <div
            class="flex flex-row w-full bg-gray-100 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8">
            <Button
              class="w-full"
              :class="
                editor.isActive('bold')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleBold().run()">
              <FeatherIcon name="bold" class="w-4" />
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('italic')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleItalic().run()">
              <FeatherIcon name="italic" class="w-4" />
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('underline')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleUnderline().run()">
              <FeatherIcon name="underline" class="w-4" />
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('strike')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleStrike().run()">
              <FeatherIcon name="/" class="w-4" />
            </Button>
          </div>

          <div class="my-4">
            <span class="font-medium text-lg">Items</span>
            <div class="flex items-stretch w-full space-x-2 justify-center">
              <Button @click="editor.chain().focus().toggleOrderedList().run()">
                <FeatherIcon name="list" class="w-4" />
              </Button>
              <Button @click="editor.chain().focus().toggleBulletList().run()">
                <FeatherIcon name="list" class="w-4" />
              </Button>
            </div>
          </div>
          <div class="my-4">
            <span class="font-medium text-lg">Alignment</span>
            <div class="flex items-stretch w-full space-x-2 justify-center">
              <Button
                @click="editor.chain().focus().setTextAlign('left').run()">
                <FeatherIcon name="align-left" class="w-4" />
              </Button>
              <Button
                @click="editor.chain().focus().setTextAlign('center').run()">
                <FeatherIcon name="align-center" class="w-4" />
              </Button>
              <Button
                @click="editor.chain().focus().setTextAlign('right').run()">
                <FeatherIcon name="align-right" class="w-4" />
              </Button>
              <Button
                @click="editor.chain().focus().setTextAlign('justify').run()">
                <FeatherIcon name="align-justify" class="w-4" />
              </Button>
            </div>
          </div>
          <div class="my-4">
            <span class="font-medium text-lg">Items</span>
            <div class="flex items-stretch w-full space-x-2 justify-center">
              <Button @click="editor.chain().focus().toggleOrderedList().run()">
                <FeatherIcon name="list" class="w-4" />
              </Button>
              <Button @click="editor.chain().focus().toggleBulletList().run()">
                <FeatherIcon name="list" class="w-4" />
              </Button>
            </div>
          </div>
          <div class="my-4">
            <span class="font-medium text-lg">Decorations</span>
            <div class="flex items-stretch w-full space-x-2 justify-center">
              <Button @click="editor.chain().focus().toggleCodeBlock().run()">
                <FeatherIcon name="code" class="w-4" />
              </Button>
              <Button @click="editor.chain().focus().toggleBlockquote().run()">
                <FeatherIcon name="message-square" class="w-4" />
              </Button>
            </div>
            <div class="p-2">
              <div class="text-sm text-gray-700">Text Color</div>
              <div class="mt-1 grid grid-cols-8 gap-1">
                <div
                  class="flex"
                  v-for="color in foregroundColors"
                  :key="color.name"
                  :text="color.name">
                  <button
                    :aria-label="color.name"
                    class="flex h-5 w-5 items-center justify-center rounded border text-base"
                    :style="{
                      color: color.hex,
                    }"
                    @click="setForegroundColor(color)">
                    A
                  </button>
                </div>
              </div>
              <div class="mt-2 text-sm text-gray-700">Background Color</div>
              <div class="mt-1 grid grid-cols-8 gap-1">
                <div
                  class="flex"
                  v-for="color in backgroundColors"
                  :key="color.name"
                  :text="color.name">
                  <button
                    :aria-label="color.name"
                    class="flex h-5 w-5 items-center justify-center rounded border text-base text-gray-900"
                    :class="
                      !color.hex ? 'border-gray-200' : 'border-transparent'
                    "
                    :style="{
                      backgroundColor: color.hex,
                    }"
                    @click="setBackgroundColor(color)">
                    A
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="tab === 3"
        class="p-4 border-b space-y-2"
        :class="
          tab === 3 ? 'flex-auto' : 'text-gray-600 cursor-pointer flex-none '
        "
        @click="tab = 3">
        <span class="font-medium text-lg">Insert</span>
        <div class="space-y-2 space-x-2">
          <Button class="h-7" @click="addImageDialog = true">Image</Button>
          <InsertImage v-model="addImageDialog" :editor="editor" />
          <Button class="h-7" @click="addVideoDialog = true">Video</Button>
          <InsertVideo v-model="addVideoDialog" :editor="editor" />
          <Button
            class="px-2"
            @click="editor.chain().focus().setHorizontalRule().run()">
            —
          </Button>
        </div>
        <div class="flex-col items-start w-full space-x-2 justify-start">
          <span class="font-medium text-lg">Table</span>
          <div class="flex items-stretch w-full space-x-2 justify-center">
            <Button
              class="px-2"
              @click="
                editor
                  .chain()
                  .focus()
                  .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
                  .run()
              ">
              Table
            </Button>
          </div>
          <div class="flex items-center w-full space-x-2 justify-center">
            <Button
              class="px-2"
              @click="editor.chain().focus().addColumnBefore().run()">
              Column Left
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().addColumnAfter().run()">
              Column Right
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().deleteColumn().run()">
              Delete Column
            </Button>
          </div>
          <div class="flex items-stretch w-full space-x-2 justify-center">
            <Button
              class="px-2"
              @click="editor.chain().focus().addRowBefore().run()">
              Row Above
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().addRowAfter().run()">
              Row Below
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().deleteRow().run()">
              Delete Row
            </Button>
          </div>
          <div class="flex items-stretch w-full space-x-2 justify-center">
            <Button
              class="px-2"
              @click="editor.chain().focus().mergeCells().run()">
              Merge Cells
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().splitCell().run()">
              Split Cells
            </Button>
          </div>
          <div class="flex items-stretch w-full space-x-2 justify-center">
            <Button
              class="px-2"
              @click="editor.chain().focus().toggleHeaderColumn().run()">
              Header Col
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().toggleHeaderRow().run()">
              Header Row
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().toggleHeaderCell().run()">
              Header Cell
            </Button>
            <Button
              class="px-2"
              @click="editor.chain().focus().deleteTable().run()">
              Delete Table
            </Button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
  <div
    class="flex flex-col items-center h-full overflow-y-hidden border-l z-0 max-w-[50px] min-w-[50px] p-2 bg-white">
    <Button
      @click="tab = 0"
      class="mb-2 py-4 text-gray-600"
      :class="[
        tab === 0 && showInfoSidebar
          ? 'text-black bg-gray-300'
          : ' hover:bg-gray-100',
      ]"
      variant="minimal">
      <FeatherIcon
        name="alert-circle"
        :class="[
          tab === 0 && showInfoSidebar
            ? 'text-black-overlay-700'
            : 'text-gray-600',
        ]"
        class="stroke-2 text-gray-600 w-full h-full" />
    </Button>
    <Button
      v-if="$route.meta.documentPage"
      @click="tab = 1"
      class="mb-2 text-gray-600 py-4"
      :class="[
        tab === 1 && showInfoSidebar
          ? 'text-black bg-gray-300'
          : ' hover:bg-gray-100',
      ]"
      variant="minimal">
      <FeatherIcon
        name="message-circle"
        :class="[
          tab === 1 && showInfoSidebar
            ? 'text-black-overlay-700'
            : 'text-gray-600',
        ]"
        class="stroke-2 text-gray-600 w-full h-full" />
    </Button>
    <Button
      v-if="$route.meta.documentPage"
      class="mb-2 text-gray-600 py-4"
      :class="[
        tab === 2 && showInfoSidebar
          ? 'text-black bg-gray-300'
          : ' hover:bg-gray-100',
      ]"
      variant="minimal"
      @click="tab = 2">
      <FeatherIcon
        name="type"
        :class="[
          tab === 2 && showInfoSidebar
            ? 'text-black-overlay-700'
            : 'text-gray-600',
        ]"
        class="stroke-2 text-gray-600 w-full h-full" />
    </Button>
    <Button
      v-if="$route.meta.documentPage"
      class="mb-2 text-gray-600 py-4"
      :class="[
        tab === 3 && showInfoSidebar
          ? 'text-black bg-gray-300'
          : ' hover:bg-gray-100',
      ]"
      variant="minimal"
      @click="tab = 3">
      <FeatherIcon
        name="plus"
        :class="[
          tab === 3 && showInfoSidebar
            ? 'text-black-overlay-700'
            : 'text-gray-600',
        ]"
        class="stroke-2 text-gray-600 w-full h-full" />
    </Button>
  </div>
</template>

<script>
import { FeatherIcon, Avatar, Input, Popover, Dropdown } from "frappe-ui";
import ShareDialog from "@/components/ShareDialog.vue";
import TagInput from "@/components/TagInput.vue";
import Tag from "@/components/Tag.vue";
import { formatMimeType, formatDate } from "@/utils/format";
import { getIconUrl } from "@/utils/getIconUrl";
import { v4 as uuidv4 } from "uuid";
import { defineAsyncComponent } from "vue";
import OuterCommentVue from "@/components/DocEditor/OuterComment.vue";

export default {
  name: "DocMenuAndInfoBar",
  components: {
    Input,
    FeatherIcon,
    Avatar,
    ShareDialog,
    TagInput,
    Tag,
    OuterCommentVue,
    Popover,
    InsertImage: defineAsyncComponent(() => import("./InsertImage.vue")),
    InsertVideo: defineAsyncComponent(() => import("./InsertVideo.vue")),
  },
  emits: ["setContentEmit", "focusContentEmit"],
  setup() {
    return { formatMimeType, getIconUrl };
  },
  inheritAttrs: false,
  inject: ["editor"],
  data() {
    return {
      tab: 0,
      newComment: "",
      showShareDialog: false,
      addImageDialog: false,
      addVideoDialog: false,
      addTag: false,
      fontSizeOptions: [
        {
          label: "Extra Small",
          action: (editor) => editor.chain().focus().setFontSize("11px").run(),
          isActive: (editor) =>
            editor.isActive("textStyle", { fontSize: "11px" }),
        },
        {
          label: "Small",
          action: (editor) => editor.chain().focus().setFontSize("13px").run(),
          isActive: (editor) =>
            editor.isActive("textStyle", { fontSize: "13px" }),
        },
        {
          label: "Normal",
          action: (editor) => editor.chain().focus().setFontSize("15px").run(),
          isActive: (editor) =>
            editor.isActive("paragraph") ||
            editor.isActive("textStyle", { fontSize: "15px" }),
        },
        {
          label: "Large",
          action: (editor) => editor.chain().focus().setFontSize("22px").run(),
          isActive: (editor) =>
            editor.isActive("textStyle", { fontSize: "22px" }),
        },
        {
          label: "Extra Large",
          action: (editor) => editor.chain().focus().setFontSize("32px").run(),
          isActive: (editor) =>
            editor.isActive("textStyle", { fontSize: "32px" }),
        },
      ],
      lineOptions: [
        {
          label: "1",
          action: (editor) =>
            editor.chain().focus().setLineHeight("100%").run(),
          isActive: (editor) => editor.isActive({ lineHeight: "100%" }),
        },
        {
          label: "1.15",
          action: (editor) =>
            editor.chain().focus().setLineHeight("115%").run(),
          isActive: (editor) => editor.isActive({ lineHeight: "115%" }),
        },
        {
          label: "1.5",
          action: (editor) =>
            editor.chain().focus().setLineHeight("150%").run(),
          isActive: (editor) => editor.isActive({ lineHeight: "150%" }),
        },
        {
          label: "2",
          action: (editor) =>
            editor.chain().focus().setLineHeight("200%").run(),
          isActive: (editor) => editor.isActive({ lineHeight: "200%" }),
        },
        {
          label: "2.5",
          action: (editor) =>
            editor.chain().focus().setLineHeight("250%").run(),
          isActive: (editor) => editor.isActive({ lineHeight: "250%" }),
        },
        {
          label: "3",
          action: (editor) =>
            editor.chain().focus().setLineHeight("300%").run(),
          isActive: (editor) => editor.isActive({ lineHeight: "300%" }),
        },
      ],
      fontFamilyOptions: [
        {
          label: "Sans Serif",
          action: (editor) =>
            editor.chain().focus().setFontFamily("Inter").run(),
          isActive: (editor) =>
            editor.isActive("textStyle", { fontFamily: "Inter" }),
        },
        {
          label: "Serif",
          action: (editor) =>
            editor.chain().focus().setFontFamily("ui-serif").run(),
          isActive: (editor) =>
            editor.isActive("textStyle", { fontFamily: "ui-serif" }),
        },
        {
          label: "Monospace",
          action: (editor) =>
            editor.chain().focus().setFontFamily("monospace").run(),
          isActive: (editor) =>
            editor.isActive("textStyle", { fontFamily: "monospace" }),
        },
      ],
    };
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id;
    },
    fullName() {
      return this.$store.state.user.fullName;
    },
    currentUserName() {
      return this.$store.state.user.fullName;
    },
    currentUserImage() {
      return this.$store.state.user.imageURL;
    },
    entity() {
      return localStorage.getItem("entityInfo");
    },
    unaddedTags() {
      return this.$resources.userTags.data.filter(
        ({ name: id1 }) =>
          !this.$resources.entityTags.data.some(({ name: id2 }) => id2 === id1)
      );
    },
    allComments() {
      console.log(this.$store.state.allComments);
      return JSON.parse(this.$store.state.allComments);
    },
    activeCommentsInstance() {
      return JSON.parse(this.$store.state.activeCommentsInstance);
    },
    showInfoSidebar() {
      return this.$store.state.showInfo;
    },
    foregroundColors() {
      // tailwind css colors, scale 600
      return [
        { name: "Default", hex: "#1F272E" },
        { name: "Yellow", hex: "#ca8a04" },
        { name: "Orange", hex: "#ea580c" },
        { name: "Red", hex: "#dc2626" },
        { name: "Green", hex: "#16a34a" },
        { name: "Blue", hex: "#1579D0" },
        { name: "Purple", hex: "#9333ea" },
        { name: "Pink", hex: "#db2777" },
      ];
    },
    backgroundColors() {
      // tailwind css colors, scale 100
      return [
        { name: "Default", hex: null },
        { name: "Yellow", hex: "#fef9c3" },
        { name: "Orange", hex: "#ffedd5" },
        { name: "Red", hex: "#fee2e2" },
        { name: "Green", hex: "#dcfce7" },
        { name: "Blue", hex: "#D3E9FC" },
        { name: "Purple", hex: "#f3e8ff" },
        { name: "Pink", hex: "#fce7f3" },
      ];
    },
  },
  watch: {
    entity() {
      if (this.entity) {
        this.$resources.userTags.fetch();
        this.$resources.entityTags.fetch();
      }
    },
  },

  methods: {
    switchTab(val) {
      if (this.$store.state.showInfo == false) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo);
        this.tab = val;
      } else if (this.tab == val) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo);
      } else {
        this.tab = val;
      }
    },
    setComment(val) {
      const localVal = val || this.commentText;
      if (!localVal.trim().length) return;
      const currentSelectedComment = JSON.parse(
        JSON.stringify(this.activeCommentsInstance)
      );
      const commentsArray =
        typeof currentSelectedComment.comments === "string"
          ? JSON.parse(currentSelectedComment.comments)
          : currentSelectedComment.comments;
      if (commentsArray) {
        commentsArray.push({
          userName: this.currentUserName,
          userImage: this.currentUserImage,
          time: Date.now(),
          content: localVal,
        });
        const commentWithUuid = JSON.stringify({
          uuid: this.activeCommentsInstance.uuid || uuidv4(),
          comments: commentsArray,
        });
        this.editor.chain().setComment(commentWithUuid).run();
        this.commentText = "";
      } else {
        const commentWithUuid = JSON.stringify({
          uuid: uuidv4(),
          comments: [
            {
              userName: this.currentUserName,
              userImage: this.currentUserImage,
              time: Date.now(),
              content: localVal,
            },
          ],
        });
        this.editor.chain().setComment(commentWithUuid).run();
        this.commentText = "";
      }
    },
    focusContent({ from, to }) {
      this.editor.chain().setTextSelection({ from, to }).run();
    },
    toggleSideBar() {
      if (this.entity) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo);
      }
    },
    setBackgroundColor(color) {
      if (color.name != "Default") {
        this.editor.chain().focus().toggleHighlight({ color: color.hex }).run();
      } else {
        this.editor.chain().focus().unsetHighlight().run();
      }
    },
    setForegroundColor(color) {
      if (color.name != "Default") {
        this.editor.chain().focus().setColor(color.hex).run();
      } else {
        this.editor.chain().focus().unsetColor().run();
      }
    },
    onButtonClick(button) {
      if (typeof button.action === "string") {
        this.emitter.emit(button.action);
      } else {
        button.action(this.editor);
      }
    },
  },
  resources: {
    userTags() {
      return {
        url: "drive.api.tags.get_user_tags",
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
        auto: false,
      };
    },
    entityTags() {
      return {
        url: "drive.api.tags.get_entity_tags",
        params: { entity: this.entity.name },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
        auto: false,
      };
    },
  },
};
</script>
