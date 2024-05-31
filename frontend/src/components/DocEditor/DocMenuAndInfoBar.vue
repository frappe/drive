<template>
  <Transition
    enter-from-class="translate-x-[150%] opacity-0"
    leave-to-class="translate-x-[150%] opacity-0"
    enter-active-class="transition duration-125"
    leave-active-class="transition duration-125"
  >
    <div
      v-if="showInfoSidebar"
      class="min-w-[352px] max-w-[352px] min-h-full border-l overflow-auto"
    >
      <div v-if="entity" class="w-full border-b pl-3 py-4">
        <div class="flex items-center">
          <div class="font-medium truncate text-lg">
            {{ entity.title }}
          </div>
        </div>
      </div>
      <div v-if="entity && editor">
        <!-- Info -->
        <div v-if="tab === 4" class="px-5 py-4 border-b">
          <span
            class="inline-flex items-center gap-2.5 mb-5 text-gray-800 font-medium text-lg w-full"
          >
            Information
          </span>
          <div class="space-y-6.5 h-full flex-auto flex flex-col z-0">
            <div v-if="entity.owner === 'You'">
              <div class="text-base font-medium mb-4">Access</div>
              <div class="flex items-center justify-start">
                <Avatar
                  size="lg"
                  :label="entity.owner"
                  :image="entity.user_image"
                ></Avatar>
                <div class="border-l h-6 mx-1.5"></div>
                <GeneralAccess
                  v-if="
                    !$resources.generalAccess.loading &&
                    (!!$resources.generalAccess.data.length ||
                      !sharedWithList.length)
                  "
                  size="lg"
                  class="-mr-[3px] outline outline-white"
                  :general-access="$resources.generalAccess?.data?.[0]"
                />
                <div
                  v-if="sharedWithList?.length"
                  class="flex items-center justify-start"
                >
                  <Avatar
                    v-for="user in sharedWithList.slice(0, 3)"
                    :key="user.user_name"
                    size="lg"
                    :label="user.full_name ? user.full_name : user.user_name"
                    :image="user.user_image"
                    class="-mr-[3px] outline outline-white"
                  />

                  <Avatar
                    v-if="sharedWithList.slice(3).length"
                    size="lg"
                    :label="sharedWithList.slice(3).length.toString()"
                    class="-mr-[3px] outline outline-white"
                  />
                </div>
              </div>
            </div>
            <!-- <div
              v-if="
                $resources.entityTags.data?.length || entity.owner === 'You'
              "
            >
              <div class="text-base font-medium mb-4">Tags</div>
              <div class="flex items-center justify-start flex-wrap gap-y-4">
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
                        userTags.fetch()
                        $resources.entityTags.fetch()
                      }
                    "
                  />
                </div>
                <span v-else class="text-gray-700 text-sm">
                  This file has no tags
                </span>
                <Button
                  v-if="!addTag && entity.owner === 'You'"
                  class="ml-auto"
                  @click="addTag = true"
                >
                  Add tag
                </Button>
                <TagInput
                  v-if="addTag"
                  :class="{ 'w-full': $resources.entityTags.data?.length }"
                  :entity="entity"
                  :unadded-tags="unaddedTags"
                  @success="
                    () => {
                      userTags.fetch()
                      $resources.entityTags.fetch()
                      addTag = false
                    }
                  "
                  @close="addTag = false"
                />
              </div>
            </div> -->
            <div>
              <div class="text-base font-medium mb-4">Properties</div>
              <div class="text-base grid grid-flow-row grid-cols-2 gap-y-3">
                <span class="col-span-1 text-gray-600">Type</span>
                <span class="col-span-1">{{ formattedMimeType }}</span>
                <span class="col-span-1 text-gray-600">Size</span>
                <span class="col-span-1">{{ entity.file_size }}</span>
                <span class="col-span-1 text-gray-600">Modified</span>
                <span class="col-span-1">{{ entity.modified }}</span>
                <span class="col-span-1 text-gray-600">Created</span>
                <span class="col-span-1">{{ entity.creation }}</span>
                <span class="col-span-1 text-gray-600">Owner</span>
                <span class="col-span-1">{{ entity.full_name }}</span>
              </div>
            </div>
            <div>
              <div class="text-base font-medium mb-4">Stats</div>
              <div class="text-base grid grid-flow-row grid-cols-2 gap-y-3">
                <span class="col-span-1 text-gray-600">Words</span>
                <span class="col-span-1">
                  {{ editor.storage.characterCount.words() }}
                </span>
                <span class="col-span-1 text-gray-600">Characters</span>
                <span class="col-span-1">
                  {{ editor.storage.characterCount.characters() }}
                </span>
                <span class="col-span-1 text-gray-600">Reading Time</span>
                <span class="col-span-1">
                  {{ Math.ceil(editor.storage.characterCount.words() / 200) }}
                  {{
                    Math.ceil(editor.storage.characterCount.words() / 200) > 1
                      ? "mins"
                      : "min"
                  }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Comments -->
        <div v-if="tab === 5" class="px-5 py-4 border-b">
          <span
            class="inline-flex items-center gap-2.5 text-gray-800 font-medium text-lg w-full"
          >
            Comments
          </span>
          <OuterCommentVue
            v-if="!!allComments.length"
            :active-comments-instance="activeCommentsInstance"
            :all-comments="allComments"
            :focus-content="focusContent"
            :is-comment-mode-on="showComments"
            @set-comment="setComment"
          />
          <div v-else class="text-gray-600 text-sm my-5">
            There are no comments for the current document
          </div>
        </div>

        <!-- Typography -->
        <div v-if="tab === 0" class="flex flex-col px-5 py-4 border-b">
          <span
            class="inline-flex items-center gap-2.5 mb-5 text-gray-800 font-medium text-lg w-full"
          >
            Style
          </span>
          <span class="font-medium text-gray-600 text-xs my-2">TITLE</span>
          <div class="w-full flex justify-between gap-x-1.5 mb-6">
            <Button
              class="w-1/3 font-semibold"
              @click="
                editor
                  .chain()
                  .focus()
                  .clearNodes()
                  .unsetAllMarks()
                  .setHeading({ level: 1 })
                  .run()
              "
            >
              Title
            </Button>
            <Button
              class="w-1/3 font-medium"
              @click="
                editor
                  .chain()
                  .focus()
                  .clearNodes()
                  .unsetAllMarks()
                  .setHeading({ level: 2 })
                  .run()
              "
            >
              Subtitle
            </Button>
            <Button
              class="w-1/3"
              @click="
                editor
                  .chain()
                  .focus()
                  .clearNodes()
                  .unsetAllMarks()
                  .setHeading({ level: 3 })
                  .run()
              "
            >
              Heading
            </Button>
          </div>

          <span class="font-semibold text-gray-600 text-xs my-2">CONTENT</span>
          <div class="w-full flex justify-between gap-x-1.5 mb-6">
            <Button
              class="w-1/3 font-bold"
              @click="
                editor
                  .chain()
                  .focus()
                  .clearNodes()
                  .unsetAllMarks()
                  .setBold()
                  .setHeading({ level: 4 })
                  .run()
              "
            >
              Strong
            </Button>
            <Button
              class="w-1/3"
              @click="
                editor
                  .chain()
                  .focus()
                  .clearNodes()
                  .unsetAllMarks()
                  .setParagraph()
                  .run()
              "
            >
              Body
            </Button>
            <Button
              class="w-1/3"
              @click="
                editor
                  .chain()
                  .focus()
                  .clearNodes()
                  .unsetAllMarks()
                  .setHeading({ level: 5 })
                  .setFontSize('0.9rem')
                  .setColor('#7c7c7c')
                  .run()
              "
            >
              Caption
            </Button>
          </div>
          <span class="font-medium text-gray-600 text-xs my-2">GROUPS</span>
          <div
            class="flex flex-row w-full bg-gray-100 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8 mb-2"
          >
            <Button
              class="w-full"
              :class="
                editor.isActive('bold') ? 'bg-white border' : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleBold().run()"
            >
              <Bold class="w-4 stroke-2" />
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('italic')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleItalic().run()"
            >
              <FeatherIcon name="italic" class="w-4 stroke-2" />
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('underline')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleUnderline().run()"
            >
              <Underline class="w-4 stroke-2" />
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('strike')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleStrike().run()"
            >
              <Strikethrough class="w-4 stroke-2" />
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('code')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleCode().run()"
            >
              <Code class="w-4 stroke-2" />
            </Button>
          </div>
          <div
            class="flex flex-row w-full bg-gray-100 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8 mb-2"
          >
            <Button
              class="w-full"
              :class="
                editor.isActive('bulletList')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleBulletList().run()"
            >
              <template #icon>
                <List class="w-4 stroke-2" />
              </template>
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('details')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="
                editor.isActive('details')
                  ? editor.chain().focus().removeDetails().run()
                  : editor.chain().focus().setDetails().run()
              "
            >
              <template #icon>
                <Details class="w-4" />
              </template>
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('orderedList')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleOrderedList().run()"
            >
              <template #icon>
                <OrderList class="w-4" />
              </template>
            </Button>
            <Button
              class="w-full"
              :class="
                editor.isActive('taskList')
                  ? 'bg-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().toggleTaskList().run()"
            >
              <template #icon>
                <Check class="w-4" />
              </template>
            </Button>
          </div>
          <div class="flex gap-x-1.5 mb-6">
            <div
              class="flex flex-row bg-gray-100 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8"
            >
              <Button
                :variant="'subtle'"
                @click="editor.chain().focus().indent().run()"
              >
                <Indent class="h-4" />
              </Button>
              <Button
                :variant="'subtle'"
                @click="editor.chain().focus().outdent().run()"
              >
                <Outdent class="h-4" />
              </Button>
            </div>
            <div
              class="flex flex-row w-full bg-gray-100 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8"
            >
              <Button
                class="w-full"
                :class="
                  editor.isActive({ textAlign: 'left' })
                    ? 'bg-white shadow-sm'
                    : 'bg-transparent'
                "
                @click="editor.chain().focus().setTextAlign('left').run()"
              >
                <alignLeft class="w-4" />
              </Button>
              <Button
                class="w-full"
                :class="
                  editor.isActive({ textAlign: 'center' })
                    ? 'bg-white shadow-sm'
                    : 'bg-transparent'
                "
                @click="editor.chain().focus().setTextAlign('center').run()"
              >
                <alignCenter class="w-4" />
              </Button>
              <Button
                class="w-full"
                :class="
                  editor.isActive({ textAlign: 'right' })
                    ? 'bg-white shadow-sm'
                    : 'bg-transparent'
                "
                @click="editor.chain().focus().setTextAlign('right').run()"
              >
                <alignRight class="w-4" />
              </Button>
              <Button
                class="w-full"
                :class="
                  editor.isActive({ textAlign: 'justify' })
                    ? 'bg-white shadow-sm'
                    : 'bg-transparent'
                "
                @click="editor.chain().focus().setTextAlign('justify').run()"
              >
                <alignJustify class="w-4" />
              </Button>
            </div>
          </div>

          <span class="font-medium text-gray-600 text-xs my-2">
            DECORATIONS
          </span>
          <div class="w-full flex justify-between gap-x-1.5 mb-6">
            <Button
              class="w-full"
              @click="editor.chain().focus().toggleCodeBlock().run()"
            >
              <template #prefix>
                <Codeblock name="code" class="w-4" />
              </template>
              Block
            </Button>
            <Button
              class="w-full"
              @click="editor.chain().focus().toggleBlockquote().run()"
            >
              <template #prefix>
                <BlockQuote name="quote" class="w-4" />
              </template>
              Focus
            </Button>
          </div>

          <span class="font-medium text-gray-600 text-xs mt-2 mb-1">
            TEXT COLOR
          </span>
          <ColorInput
            class="mt-0.5 mb-1"
            :value="editor.getAttributes('textStyle').color"
            @change="(value) => editor.chain().focus().setColor(value).run()"
          />
          <span class="font-medium text-gray-600 text-xs mt-2 mb-1">
            BACKGROUND COLOR
          </span>
          <ColorInput
            class="mt-0.5 mb-6"
            :value="editor.getAttributes('textStyle').backgroundColor"
            @change="
              (value) => editor.chain().focus().toggleHighlight(value).run()
            "
          />
          <span class="font-medium text-gray-600 text-xs my-2">FONT</span>
          <div class="w-full flex justify-between gap-x-1.5">
            <Button
              class="w-1/3"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'InterVar' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="editor.chain().focus().setFontFamily('InterVar').run()"
            >
              Sans
            </Button>
            <Button
              class="w-1/3 font-['Lora']"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'Lora' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="editor.chain().focus().setFontFamily('Lora').run()"
            >
              Serif
            </Button>
            <Button
              class="w-1/3"
              :style="{ fontFamily: 'Geist Mono' }"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'Geist Mono' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="editor.chain().focus().setFontFamily('Geist Mono').run()"
            >
              Mono
            </Button>
            <Button
              class="w-1/3 font-['Nunito']"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'Nunito' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="editor.chain().focus().setFontFamily('Nunito').run()"
            >
              Round
            </Button>
          </div>
        </div>

        <!-- Insert -->
        <div v-if="tab === 1" class="flex flex-col px-5 py-4 border-b">
          <span
            class="inline-flex items-center gap-2.5 mb-5 text-gray-800 font-medium text-lg w-full"
          >
            Insert
          </span>
          <div>
            <span class="font-medium text-gray-600 text-base mb-1">Media</span>
            <div class="w-full flex justify-between gap-x-1.5 mb-6">
              <Button
                class="w-full justify-start"
                @click="addImageDialog = true"
              >
                <template #prefix>
                  <Image class="text-gray-700 w-4" />
                  Image
                </template>
              </Button>
              <InsertImage v-model="addImageDialog" :editor="editor" />

              <Button
                class="w-full justify-start"
                @click="addVideoDialog = true"
              >
                <template #prefix>
                  <Video class="text-gray-700 w-4" />
                  Video
                </template>
              </Button>
              <InsertVideo v-model="addVideoDialog" :editor="editor" />
            </div>
          </div>
          <span class="font-medium text-gray-600 text-base mb-1">Break</span>
          <div class="w-full flex justify-between gap-x-1.5 mb-6">
            <Button
              class="w-full px-2"
              @click="editor.chain().focus().setHorizontalRule().run()"
            >
              <template #prefix>
                <Minus class="stroke-[1] text-gray-700" />
              </template>
              Rule
            </Button>

            <Button
              class="px-2 w-full"
              @click="editor.chain().focus().setPageBreak().run()"
            >
              <template #prefix>
                <svg
                  class="w-3.5"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 22H17.5C18.0304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V18M4 8V4C4 3.46957 4.21071 2.96086 4.58579 2.58579C4.96086 2.21071 5.46957 2 6 2H14.5L20 7.5V10.5"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M4 4C4 3.46957 4.21071 2.96086 4.58579 2.58579C4.96086 2.21071 5.46957 2 6 2H14.5L20 7.5M4 20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M14 2V8H20"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M3 15H21"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </template>
              Page Break
            </Button>
          </div>
          <span class="font-medium text-gray-600 text-base">Table</span>
          <div class="flex space-x-2 my-2">
            <Button
              class="w-full"
              @click="
                editor
                  .chain()
                  .focus()
                  .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
                  .run()
              "
            >
              <template #prefix>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="w-4"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  stroke-width="2"
                  stroke="currentColor"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <path
                    d="M12.5 21h-7.5a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v7.5"
                  ></path>
                  <path d="M3 10h18"></path>
                  <path d="M10 3v18"></path>
                  <path d="M16 19h6"></path>
                  <path d="M19 16v6"></path>
                </svg>
                New Table
              </template>
            </Button>
            <Button
              v-if="editor.can().deleteTable()"
              class="w-full"
              @click="editor.chain().focus().deleteTable().run()"
            >
              <template #prefix>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="w-4"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  stroke-width="2"
                  stroke="currentColor"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <path
                    d="M12.5 21h-7.5a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v10"
                  ></path>
                  <path d="M3 10h18"></path>
                  <path d="M10 3v18"></path>
                  <path d="M16 19h6"></path>
                </svg>
                Delete Table
              </template>
            </Button>
          </div>

          <div v-if="editor.can().deleteTable()" class="space-y-2">
            <span class="font-medium text-gray-600 text-base">Row</span>
            <div class="flex items-stretch w-full space-x-2 justify-center">
              <Button
                class="px-2 w-full"
                @click="editor.chain().focus().addRowBefore().run()"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="icon icon-tabler icon-tabler-row-insert-top"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  stroke-width="1"
                  stroke="currentColor"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <path
                    d="M4 18v-4a1 1 0 0 1 1 -1h14a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-14a1 1 0 0 1 -1 -1z"
                  ></path>
                  <path d="M12 9v-4"></path>
                  <path d="M10 7l4 0"></path>
                </svg>
              </Button>
              <Button
                class="px-2 w-full"
                @click="editor.chain().focus().addRowAfter().run()"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="icon icon-tabler icon-tabler-row-insert-bottom"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  stroke-width="1"
                  stroke="currentColor"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <path
                    d="M20 6v4a1 1 0 0 1 -1 1h-14a1 1 0 0 1 -1 -1v-4a1 1 0 0 1 1 -1h14a1 1 0 0 1 1 1z"
                  ></path>
                  <path d="M12 15l0 4"></path>
                  <path d="M14 17l-4 0"></path>
                </svg>
              </Button>
              <Button
                class="px-2 w-full"
                @click="editor.chain().focus().deleteRow().run()"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="icon icon-tabler icon-tabler-row-remove"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  stroke-width="1"
                  stroke="currentColor"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <path
                    d="M20 6v4a1 1 0 0 1 -1 1h-14a1 1 0 0 1 -1 -1v-4a1 1 0 0 1 1 -1h14a1 1 0 0 1 1 1z"
                  ></path>
                  <path d="M10 16l4 4"></path>
                  <path d="M10 20l4 -4"></path>
                </svg>
              </Button>
            </div>

            <div class="space-y-2">
              <span class="font-medium text-gray-600 text-base my-4">
                Column
              </span>
              <div class="flex items-stretch w-full space-x-2 justify-center">
                <Button
                  class="px-2 w-full"
                  @click="editor.chain().focus().addColumnBefore().run()"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="icon icon-tabler icon-tabler-column-insert-left"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    stroke-width="1"
                    stroke="currentColor"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <path
                      d="M14 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1z"
                    ></path>
                    <path d="M5 12l4 0"></path>
                    <path d="M7 10l0 4"></path>
                  </svg>
                </Button>
                <Button
                  class="w-full text-gray-600"
                  @click="editor.chain().focus().addColumnAfter().run()"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="icon icon-tabler icon-tabler-column-insert-right"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    stroke-width="1"
                    stroke="currentColor"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <path
                      d="M6 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1z"
                    ></path>
                    <path d="M15 12l4 0"></path>
                    <path d="M17 10l0 4"></path>
                  </svg>
                </Button>
                <Button
                  class="px-2 w-full"
                  @click="editor.chain().focus().deleteColumn().run()"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="icon icon-tabler icon-tabler-column-remove"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    stroke-width="1"
                    stroke="currentColor"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <path
                      d="M6 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1z"
                    ></path>
                    <path d="M16 10l4 4"></path>
                    <path d="M16 14l4 -4"></path>
                  </svg>
                </Button>
              </div>
            </div>
            <div class="space-y-2">
              <span class="font-medium text-gray-600 text-base">Cells</span>
              <div class="flex items-stretch w-full space-x-2 justify-center">
                <Button
                  class="px-2 w-full"
                  @click="editor.chain().focus().mergeCells().run()"
                >
                  <template #prefix>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="w-4"
                      fill="currentColor"
                      stroke="currentColor"
                      stroke-width="0"
                      viewBox="0 0 24 24"
                      width="24"
                      height="24"
                    >
                      <path
                        d="M21 20C21 20.5523 20.5523 21 20 21H4C3.44772 21 3 20.5523 3 20V4C3 3.44772 3.44772 3 4 3H20C20.5523 3 21 3.44772 21 4V20ZM19 11V5H13.001V7H15L12 10L9 7H11V5H5V11H7V13H5V19H11V17H9L12 14L15 17H13.001V19H19V13H17V11H19ZM11 13H9V11H11V13ZM15 13H13V11H15V13Z"
                      ></path>
                    </svg>
                  </template>
                  Merge
                </Button>
                <Button
                  class="px-2 w-full"
                  @click="editor.chain().focus().splitCell().run()"
                >
                  <template #prefix>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="w-4"
                      fill="currentColor"
                      stroke="currentColor"
                      stroke-width="0"
                      viewBox="0 0 24 24"
                      width="24"
                      height="24"
                    >
                      <path
                        d="M21 20C21 20.5523 20.5523 21 20 21H4C3.44772 21 3 20.5523 3 20V4C3 3.44772 3.44772 3 4 3H20C20.5523 3 21 3.44772 21 4V20ZM19 11V5H13.001V7H15L12 10L9 7H11V5H5V11H7V13H5V19H11V17H9L12 14L15 17H13.001V19H19V13H17V11H19ZM11 13H9V11H11V13ZM15 13H13V11H15V13Z"
                      ></path>
                    </svg>
                  </template>
                  Split
                </Button>
                <Button
                  class="px-2 w-full"
                  @click="editor.chain().focus().toggleHeaderCell().run()"
                >
                  <template #prefix>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="w-4"
                      fill="currentColor"
                      stroke="currentColor"
                      stroke-width="0"
                      viewBox="0 0 24 24"
                      width="24"
                      height="24"
                    >
                      <path
                        d="M15 21H9V10H15V21ZM17 21V10H22V20C22 20.5523 21.5523 21 21 21H17ZM7 21H3C2.44772 21 2 20.5523 2 20V10H7V21ZM22 8H2V4C2 3.44772 2.44772 3 3 3H21C21.5523 3 22 3.44772 22 4V8Z"
                        fill="currentColor"
                      ></path>
                    </svg>
                  </template>
                  Header
                </Button>
              </div>
            </div>
          </div>
          <!--         <div class="flex-col items-start w-full space-x-2 justify-start">
            <span class="font-medium text-gray-600 text-base">Header</span>
            <div class="flex items-stretch w-full space-x-2 justify-center">   
            </div>
            <div class="flex items-stretch w-full space-x-2 justify-center">
              <Button
                class="px-2"
                @click="editor.chain().focus().toggleHeaderColumn().run()">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-table-column" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <path d="M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14z"></path>
                    <path d="M10 10h11"></path>
                    <path d="M10 3v18"></path>
                    <path d="M9 3l-6 6"></path>
                    <path d="M10 7l-7 7"></path>
                    <path d="M10 12l-7 7"></path>
                    <path d="M10 17l-4 4"></path>
                  </svg>
              </template>
                Header Col
              </Button>
              <Button
                class="px-2"
                @click="editor.chain().focus().toggleHeaderRow().run()">
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-table-row" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <path d="M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14z"></path>
                    <path d="M9 3l-6 6"></path>
                    <path d="M14 3l-7 7"></path>
                    <path d="M19 3l-7 7"></path>
                    <path d="M21 6l-4 4"></path>
                    <path d="M3 10h18"></path>
                    <path d="M10 10v11"></path>
                  </svg>
              </template>
                Header Row
              </Button>
            </div>
          </div> -->
        </div>

        <!-- Document Settings -->
        <div v-if="tab === 2" class="flex flex-col px-5 py-4 border-b">
          <span
            class="inline-flex items-center gap-2.5 mb-5 text-gray-800 font-medium text-lg w-full"
          >
            Settings
          </span>
          <div class="flex items-center">
            <span class="font-medium text-gray-700 text-base my-2">
              Small Text
            </span>
            <Switch
              v-model="settings.docSize"
              :class="settings.docSize ? 'bg-black' : 'bg-gray-200'"
              class="ml-auto auto inline-flex h-4 w-[26px] items-center rounded-full cursor-pointer"
              @click="settings.docSize = !settings.docSize"
            >
              <span
                :class="settings.docSize ? 'translate-x-3.5' : 'translate-x-1'"
                class="inline-block h-2 w-2 transform rounded-full bg-white transition"
              />
            </Switch>
          </div>
          <div class="flex items-center">
            <span class="font-medium text-gray-700 text-base my-2">
              Full Width
            </span>
            <Switch
              v-model="settings.docWidth"
              :class="settings.docWidth ? 'bg-black' : 'bg-gray-200'"
              class="ml-auto auto inline-flex h-4 w-[26px] items-center rounded-full cursor-pointer"
              @click="settings.docWidth = !settings.docWidth"
            >
              <span
                :class="settings.docWidth ? 'translate-x-3.5' : 'translate-x-1'"
                class="inline-block h-2 w-2 transform rounded-full bg-white transition"
              />
            </Switch>
          </div>
          <span class="font-medium text-gray-700 text-base my-2">
            Default Font
          </span>
          <div class="w-full flex justify-between gap-1">
            <Button
              class="w-1/3"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'InterVar' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="settings.docFont = 'font-fd-sans'"
            >
              Sans
            </Button>
            <Button
              class="w-1/3 font-['Lora']"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'Lora' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="settings.docFont = 'font-fd-serif'"
            >
              Serif
            </Button>
            <Button
              class="w-1/3"
              :style="{ fontFamily: 'Geist Mono' }"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'Geist Mono' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="settings.docFont = 'font-fd-mono'"
            >
              Mono
            </Button>
            <Button
              class="w-1/3 font-['Nunito']"
              :class="[
                editor.isActive('textStyle', { fontFamily: 'Nunito' })
                  ? 'outline outline-gray-400'
                  : '',
              ]"
              @click="settings.docFont = 'font-fd-round'"
            >
              Round
            </Button>
          </div>
        </div>

        <!-- Transform -->
        <div v-if="tab === 3" class="px-5 py-4 border-b">
          <span
            class="inline-flex items-center gap-2.5 mb-5 text-gray-800 font-medium text-lg w-full"
          >
            Transform
          </span>
          <div>
            <span
              v-if="$route.meta.documentPage && $store.state.hasWriteAccess"
              class="font-medium text-gray-700 text-base"
            >
              Import
            </span>
            <Button
              v-if="$route.meta.documentPage && $store.state.hasWriteAccess"
              class="w-full justify-start mb-2"
              @click="() => emitter.emit('importDocFromWord')"
            >
              <template #prefix>
                <FileUp class="text-gray-700 w-4 stroke-[1.5]" />
                Import DOCX
              </template>
            </Button>
            <span class="font-medium text-gray-700 text-base">Export</span>
            <Button
              class="w-full justify-start"
              @click="() => emitter.emit('exportDocToPDF')"
            >
              <template #prefix>
                <FileDown class="text-gray-700 w-4 stroke-[1.5]" />
                Export PDF
              </template>
            </Button>
            <!-- <Button class="w-full justify-start">
            <template #prefix>
              <FileDown class="text-gray-700 w-4" />
              Export to DOCX
            </template>
          </Button> -->
          </div>
        </div>
      </div>
    </div>
  </Transition>
  <div
    class="hidden sm:flex flex-col items-center overflow-hidden h-full min-w-[48px] gap-1 pt-3 px-0 border-l z-0 bg-white"
  >
    <template v-for="(item, index) in tabs" :key="item.label">
      <button
        v-if="item.write === $store.state.hasWriteAccess || !item.write"
        variant="'ghost'"
        :class="[
          tab === index && showInfoSidebar
            ? 'text-black bg-gray-200'
            : ' hover:bg-gray-50',
        ]"
        class="h-7 w-7 text-gray-600 rounded"
        @click="switchTab(index)"
      >
        <component
          :is="item.icon"
          :class="[
            tab === 1 && showInfoSidebar ? 'text-gray-700' : 'text-gray-600',
          ]"
          class="mx-auto stroke-[1.5] text-gray-600 w-4 h-4"
        />
      </button>
    </template>
  </div>
</template>

<script>
import { FeatherIcon, Avatar, Input, Popover, Badge, Dropdown } from "frappe-ui"
import TagInput from "@/components/TagInput.vue"
import Tag from "@/components/Tag.vue"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { v4 as uuidv4 } from "uuid"
import { defineAsyncComponent } from "vue"
import OuterCommentVue from "@/components/DocEditor/OuterComment.vue"
import LineHeight from "./icons/line-height.vue"
import {
  Plus,
  Minus,
  Heading1,
  Heading2,
  Heading3,
  FileUp,
  FileDown,
  ArrowDownUp,
  TextQuote,
  Info,
  MessageCircle,
  FileText,
} from "lucide-vue-next"
import { Code } from "lucide-vue-next"
import { Code2 } from "lucide-vue-next"
import { ImagePlus } from "lucide-vue-next"
import { FileVideo } from "lucide-vue-next"
import { Table2Icon } from "lucide-vue-next"
import "@fontsource/lora"
import "@fontsource/geist-mono"
import "@fontsource/nunito"
import ColorInput from "./ColorInput.vue"
import Bold from "./icons/Bold.vue"
import Strikethrough from "./icons/StrikeThrough.vue"
import Underline from "./icons/Underline.vue"
import GeneralAccess from "@/components/GeneralAccess.vue"
import Indent from "./icons/Indent.vue"
import Outdent from "./icons/Outdent.vue"
import Codeblock from "./icons/Codeblock.vue"
import List from "./icons/List.vue"
import OrderList from "./icons/OrderList.vue"
import Check from "./icons/Check.vue"
import Details from "./icons/Details.vue"
import alignRight from "./icons/AlignRight.vue"
import alignLeft from "./icons/AlignLeft.vue"
import alignCenter from "./icons/AlignCenter.vue"
import alignJustify from "./icons/AlignJustify.vue"
import BlockQuote from "./icons/BlockQuote.vue"
import Style from "./icons/Style.vue"
import Image from "./icons/Image.vue"
import Video from "./icons/Video.vue"

export default {
  name: "DocMenuAndInfoBar",
  components: {
    Input,
    FeatherIcon,
    Avatar,
    TagInput,
    Tag,
    OuterCommentVue,
    Popover,
    InsertImage: defineAsyncComponent(() => import("./InsertImage.vue")),
    InsertVideo: defineAsyncComponent(() => import("./InsertVideo.vue")),
    LineHeight,
    Plus,
    Minus,
    Bold,
    Strikethrough,
    Underline,
    List,
    Indent,
    Outdent,
    Code,
    Code2,
    Codeblock,
    Check,
    OrderList,
    alignLeft,
    alignRight,
    alignCenter,
    alignJustify,
    BlockQuote,
    Style,
    Image,
    Video,
    Table2Icon,
    Badge,
    Dropdown,
    ColorInput,
    Heading1,
    Heading2,
    Heading3,
    FileUp,
    FileDown,
    ArrowDownUp,
    Info,
    TextQuote,
    MessageCircle,
    FileText,
    Details,
    GeneralAccess,
  },
  inject: ["editor"],
  inheritAttrs: false,
  props: {
    settings: {
      type: Object,
      required: true,
    },
  },
  setup() {
    return { formatMimeType, getIconUrl }
  },
  data() {
    return {
      tab: this.entity?.write ? 0 : 4,
      tabs: [
        {
          name: "Typography",
          icon: Style,
          write: true,
        },
        {
          name: "Insert",
          icon: Plus,
          write: true,
        },
        {
          name: "Document Settings",
          icon: FileText,
          write: true,
        },
        {
          name: "Transforms",
          icon: ArrowDownUp,
          write: false,
        },
        {
          name: "Information",
          icon: Info,
          write: false,
        },
        {
          name: "Comments",
          icon: MessageCircle,
          write: false,
        },
      ],
      newComment: "",
      showShareDialog: false,
      addImageDialog: false,
      addVideoDialog: false,
      addTag: false,
    }
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    fullName() {
      return this.$store.state.user.fullName
    },
    currentUserName() {
      return this.$store.state.user.fullName
    },
    currentUserImage() {
      return this.$store.state.user.imageURL
    },
    entity() {
      return this.$store.state.entityInfo[0]
    },
    unaddedTags() {
      return this.$resources.userTags.data.filter(
        ({ name: id1 }) =>
          !this.$resources.entityTags.data.some(({ name: id2 }) => id2 === id1)
      )
    },
    allComments() {
      return JSON.parse(this.$store.state.allComments)
    },
    activeCommentsInstance() {
      return JSON.parse(this.$store.state.activeCommentsInstance)
    },
    showInfoSidebar() {
      return this.$store.state.showInfo
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
      ]
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
      ]
    },
    showComments() {
      if (this.entity?.owner === "You") {
        return true
      } else if (this.entity.write) {
        return true
      } else if (this.entity.allow_comments) {
        return true
      } else {
        return false
      }
    },
    sharedWithList() {
      return this.$resources.userList.data?.users.concat(
        this.$resources.groupList.data
      )
    },
  },
  methods: {
    switchTab(val) {
      if (this.$store.state.showInfo == false) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo)
        this.tab = val
      } else if (this.tab == val) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo)
      } else {
        this.tab = val
      }
    },
    setComment(val) {
      const localVal = val || this.commentText
      if (!localVal.trim().length) return
      const currentSelectedComment = JSON.parse(
        JSON.stringify(this.activeCommentsInstance)
      )
      const commentsArray =
        typeof currentSelectedComment.comments === "string"
          ? JSON.parse(currentSelectedComment.comments)
          : currentSelectedComment.comments
      if (commentsArray) {
        commentsArray.push({
          userName: this.currentUserName,
          userImage: this.currentUserImage,
          time: Date.now(),
          content: localVal,
        })
        const commentWithUuid = JSON.stringify({
          uuid: this.activeCommentsInstance.uuid || uuidv4(),
          comments: commentsArray,
        })
        this.editor.chain().setComment(commentWithUuid).run()
        this.commentText = ""
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
        })
        this.editor.chain().setComment(commentWithUuid).run()
        this.commentText = ""
      }
    },
    focusContent({ from, to }) {
      this.editor.chain().setTextSelection({ from, to }).run()
    },
    toggleSideBar() {
      if (this.entity) {
        this.$store.commit("setShowInfo", !this.$store.state.showInfo)
      }
    },
    setBackgroundColor(color) {
      if (color.name != "Default") {
        this.editor.chain().focus().toggleHighlight(color.hex).run()
      } else {
        this.editor.chain().focus().unsetHighlight().run()
      }
    },
    setForegroundColor(color) {
      if (color.name != "Default") {
        this.editor.chain().focus().setColor(color.hex).run()
      } else {
        this.editor.chain().focus().unsetColor().run()
      }
    },
    onButtonClick(button) {
      if (typeof button.action === "string") {
        this.emitter.emit(button.action)
      } else {
        button.action(this.editor)
      }
    },
  },
  resources: {
    userList() {
      return {
        url: "drive.api.permissions.get_shared_with_list",
        params: { entity_name: this.entity.name },
        auto: this.entity.owner === "You",
      }
    },
    groupList() {
      return {
        url: "drive.api.permissions.get_shared_user_group_list",
        params: { entity_name: this.entity.name },
        auto: this.entity.owner === "You",
      }
    },
    generalAccess() {
      return {
        url: "drive.api.permissions.get_general_access",
        params: { entity_name: this.entity.name },
        auto: this.entity.owner === "You",
      }
    },
    userTags() {
      return {
        url: "drive.api.tags.get_user_tags",
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
        auto: false,
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
        auto: false,
      }
    },
  },
}
</script>
