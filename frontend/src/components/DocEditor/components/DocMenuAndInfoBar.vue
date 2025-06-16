<template>
  <div
    class="transition-all duration-200 ease-in-out h-full border-l overflow-y-auto"
    :class="
      showInfoSidebar
        ? 'sm:min-w-[352px] sm:max-w-[352px] min-w-full opacity-100'
        : 'w-0 min-w-0 max-w-0 overflow-hidden opacity-0'
    "
  >
    <div
      v-if="entity"
      class="w-full border-b px-5 py-4"
    >
      <div class="flex items-center">
        <div class="font-medium truncate text-lg">
          {{ entity.title }}
        </div>
      </div>
    </div>
    <div v-if="entity && editor">
      <!-- Info -->
      <div
        v-if="tab === 4"
        class="px-5 py-4 border-b"
      >
        <span
          class="inline-flex items-center gap-2.5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          {{ __("Information") }}
        </span>
        <div class="space-y-6.5 h-full flex-auto flex flex-col z-0">
          <div v-if="entity.owner === 'You'">
            <div class="text-base font-medium mb-4">Access</div>
            <div class="flex items-center justify-start">
              <Avatar
                size="md"
                :label="entity.owner"
                :image="entity.user_image"
              />
              <div class="border-l h-6 mx-1.5" />
              <GeneralAccess
                size="lg"
                class="col-span-1 justify-self-start row-start-1 row-end-1"
                :access-type="generalAccess?.access?.value"
              />
              <div
                v-if="sharedWithList?.length"
                class="flex items-center justify-start"
              >
                <Avatar
                  v-for="user in sharedWithList.slice(0, 3)"
                  :key="user?.user_name"
                  size="md"
                  :label="user?.full_name ? user?.full_name : user?.user_name"
                  :image="user?.user_image"
                  class="-mr-[3px] outline outline-white"
                />

                <Avatar
                  v-if="sharedWithList.slice(3).length"
                  size="md"
                  :label="sharedWithList.slice(3).length.toString()"
                  class="-mr-[3px] outline outline-white"
                />
              </div>
            </div>
          </div>
          <div
            v-if="$resources.entityTags.data?.length || entity.owner === 'You'"
          >
            <div class="text-base font-medium mb-4">Tags</div>
            <TagInput
              class="min-w-full"
              :entity="entity"
            />
          </div>
          <div>
            <div class="text-base font-medium mb-4">Properties</div>
            <div class="text-base grid grid-flow-row grid-cols-2 gap-y-3">
              <span class="col-span-1 text-ink-gray-5">{{ __("Type") }}</span>
              <span class="col-span-1">Frappe Doc</span>
              <span class="col-span-1 text-ink-gray-5">{{ __("Size") }}</span>
              <span class="col-span-1">{{ formatSize(entity.file_size) }}</span>
              <span class="col-span-1 text-ink-gray-5">{{
                __("Modified")
              }}</span>
              <span class="col-span-1">{{ formatDate(entity.modified) }}</span>
              <span class="col-span-1 text-ink-gray-5">{{
                __("Created")
              }}</span>
              <span class="col-span-1">{{ formatDate(entity.creation) }}</span>
              <span class="col-span-1 text-ink-gray-5">{{ __("Owner") }}</span>
              <span class="col-span-1">{{ entity.full_name }}</span>
            </div>
          </div>
          <div>
            <div class="text-base font-medium mb-4">
              {{ __("Statistics") }}
            </div>
            <div class="text-base grid grid-flow-row grid-cols-2 gap-y-3">
              <span class="col-span-1 text-ink-gray-5">{{ __("Words") }}</span>
              <span class="col-span-1">
                {{ editor.storage.characterCount.words() }}
              </span>
              <span class="col-span-1 text-ink-gray-5">{{
                __("Characters")
              }}</span>
              <span class="col-span-1">
                {{ editor.storage.characterCount.characters() }}
              </span>
              <span class="col-span-1 text-ink-gray-5">{{
                __("Reading Time")
              }}</span>
              <span class="col-span-1">
                {{ Math.ceil(editor.storage.characterCount.words() / 200) }}
                {{
                  Math.ceil(editor.storage.characterCount.words() / 200) > 1
                    ? __("minutes")
                    : __("minute")
                }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Comments -->
      <div
        v-if="tab === 5"
        class="px-5 py-4 border-b"
      >
        <AnnotationList
          v-if="allAnnotations"
          :active-annotation="activeAnnotation"
          :all-annotations="allAnnotations"
          :show-annotations="showComments"
          @set-active-annotation="setActiveAnnotation"
        />
      </div>

      <!-- Versions -->
      <div
        v-if="tab === 6"
        class="px-2 py-4 border-b"
      >
        <span
          class="px-3 inline-flex items-center gap-2.5 text-ink-gray-8 font-medium text-lg w-full"
        >
          Versions
          <Button
            class="ml-auto"
            @click="generateSnapshot"
            >New</Button
          >
        </span>
        <div
          v-if="
            !$resources.getversionList.loading &&
            $resources.getversionList.data.length
          "
        >
          <div
            v-for="(version, i) in $resources.getversionList.data"
            :key="version.name"
            class="flex flex-col gap-y-1.5 p-2 m-2 hover:bg-surface-gray-2 cursor-pointer rounded"
            @click.stop="previewSnapshot(i)"
          >
            <span
              :title="version.creation"
              class="font-medium text-base text-ink-gray-8"
            >
              {{ version.relativeTime }}
            </span>
            <span class="text-sm text-ink-gray-7">
              {{ version.snapshot_message }}
            </span>
          </div>
        </div>
        <div
          v-else
          class="text-ink-gray-5 text-sm my-5 px-3"
        >
          No previous versions available for the current document
        </div>
      </div>

      <!-- Activity -->
      <div
        v-if="tab === 7 && userId !== 'Guest'"
        class="max-h-[90vh] pt-4 pb-5 border-b overflow-y-auto overflow-x-hidden"
      >
        <span
          class="inline-flex items-center gap-2.5 px-5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          Activity
        </span>
        <ActivityTree v-if="showActivity" />
      </div>

      <!-- Typography -->
      <div
        v-if="tab === 0"
        class="flex flex-col px-5 py-4 border-b"
      >
        <span
          class="inline-flex items-center gap-2.5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          Style
        </span>
        <span class="font-medium text-ink-gray-5 text-xs my-2">TITLE</span>
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

        <span class="font-medium text-ink-gray-5 text-xs my-2">CONTENT</span>
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
        <span class="font-medium text-ink-gray-5 text-xs my-2">GROUPS</span>
        <div
          class="flex flex-row w-full bg-surface-gray-2 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8 mb-2"
        >
          <Button
            class="w-full"
            :class="
              editor.isActive('bold')
                ? 'bg-surface-white border'
                : 'bg-transparent'
            "
            @click="editor.chain().focus().toggleBold().run()"
          >
            <Bold class="w-4 stroke-2" />
          </Button>
          <Button
            class="w-full"
            :class="
              editor.isActive('italic')
                ? 'bg-surface-white shadow-sm'
                : 'bg-transparent'
            "
            @click="editor.chain().focus().toggleItalic().run()"
          >
            <LucideItalic class="w-4 stroke-2" />
          </Button>
          <Button
            class="w-full"
            :class="
              editor.isActive('underline')
                ? 'bg-surface-white shadow-sm'
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
                ? 'bg-surface-white shadow-sm'
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
                ? 'bg-surface-white shadow-sm'
                : 'bg-transparent'
            "
            @click="editor.chain().focus().toggleCode().run()"
          >
            <Code class="w-4 stroke-2" />
          </Button>
        </div>
        <div
          class="flex flex-row w-full bg-surface-gray-2 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8 mb-2"
        >
          <Button
            class="w-full"
            :class="
              editor.isActive('bulletList')
                ? 'bg-surface-white shadow-sm'
                : 'bg-transparent'
            "
            @click="editor.chain().focus().toggleBulletList().run()"
          >
            <template #icon>
              <List class="w-4 stroke-2" />
            </template>
          </Button>
          <!--             <Button
              class="w-full"
              :class="
                editor.isActive('details')
                  ? 'bg-surface-white shadow-sm'
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
            </Button> -->
          <Button
            class="w-full"
            :class="
              editor.isActive('orderedList')
                ? 'bg-surface-white shadow-sm'
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
                ? 'bg-surface-white shadow-sm'
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
            class="flex flex-row bg-surface-gray-2 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8"
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
            class="flex flex-row w-full bg-surface-gray-2 justify-stretch items-stretch rounded p-0.5 space-x-0.5 h-8"
          >
            <Button
              class="w-full"
              :class="
                editor.isActive({ textAlign: 'left' })
                  ? 'bg-surface-white shadow-sm'
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
                  ? 'bg-surface-white shadow-sm'
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
                  ? 'bg-surface-white shadow-sm'
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
                  ? 'bg-surface-white shadow-sm'
                  : 'bg-transparent'
              "
              @click="editor.chain().focus().setTextAlign('justify').run()"
            >
              <alignJustify class="w-4" />
            </Button>
          </div>
        </div>

        <span class="font-medium text-ink-gray-5 text-xs my-2">
          DECORATIONS
        </span>
        <div class="w-full flex justify-between gap-x-1.5 mb-6">
          <Button
            class="w-full"
            @click="editor.chain().focus().toggleCodeBlock().run()"
          >
            <template #prefix>
              <Codeblock
                name="code"
                class="w-4"
              />
            </template>
            Block
          </Button>
          <Button
            class="w-full"
            @click="editor.chain().focus().toggleBlockquote().run()"
          >
            <template #prefix>
              <BlockQuote
                name="quote"
                class="w-4"
              />
            </template>
            Focus
          </Button>
        </div>

        <span class="font-medium text-ink-gray-5 text-xs mt-2 mb-1">
          TEXT COLOR
        </span>
        <ColorInput
          class="mt-0.5 mb-1"
          :value="editor.getAttributes('textStyle').color"
          @change="(value) => editor.chain().focus().setColor(value).run()"
        />
        <span class="font-medium text-ink-gray-5 text-xs mt-2 mb-1">
          BACKGROUND COLOR
        </span>
        <ColorInput
          class="mt-0.5 mb-6"
          :value="editor.getAttributes('textStyle').backgroundColor"
          @change="
            (value) => editor.chain().focus().toggleHighlight(value).run()
          "
        />
        <span class="font-medium text-ink-gray-5 text-xs my-2">FONT</span>
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
      <div
        v-if="tab === 1"
        class="flex flex-col px-5 py-4 border-b"
      >
        <span
          class="inline-flex items-center gap-2.5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          Insert
        </span>
        <div>
          <span class="font-medium text-ink-gray-5 text-base mb-1">Media</span>
          <div class="w-full flex justify-between gap-x-1.5 mb-6">
            <Button
              class="w-full justify-start"
              @click="addImageDialog = true"
            >
              <template #prefix>
                <Image class="text-ink-gray-7 w-4" />
                Image
              </template>
            </Button>

            <Button
              class="w-full justify-start"
              @click="addVideoDialog = true"
            >
              <template #prefix>
                <Video class="text-ink-gray-7 w-4" />
                Video
              </template>
            </Button>
          </div>
        </div>
        <span class="font-medium text-ink-gray-5 text-base mb-1">Break</span>
        <div class="w-full flex justify-between gap-x-1.5 mb-6">
          <Button
            class="w-full px-2"
            @click="editor.chain().focus().setHorizontalRule().run()"
          >
            <template #prefix>
              <Minus class="stroke-[1] text-ink-gray-7" />
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
        <span class="font-medium text-ink-gray-5 text-base">Table</span>
        <div class="flex space-x-2 my-2">
          <Button
            :disabled="editor.isActive('table')"
            class="w-full"
            @click="
              editor
                .chain()
                .focus()
                .insertTable({ rows: 3, cols: 3, withHeaderRow: false })
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
                stroke-width="1.5"
                stroke="currentColor"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path
                  stroke="none"
                  d="M0 0h24v24H0z"
                  fill="none"
                />
                <path
                  d="M12.5 21h-7.5a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v7.5"
                />
                <path d="M3 10h18" />
                <path d="M10 3v18" />
                <path d="M16 19h6" />
                <path d="M19 16v6" />
              </svg>
              New Table
            </template>
          </Button>
        </div>
      </div>

      <!-- Document Settings -->
      <div
        v-if="tab === 2"
        class="flex flex-col px-3 py-4 border-b"
      >
        <span
          class="inline-flex items-center gap-2.5 mb-5 text-ink-gray-8 font-medium text-lg w-full px-2"
        >
          Settings
        </span>
        <Switch
          v-model="settings.docSize"
          label="Small Text"
        />
        <Switch
          v-model="settings.docSpellcheck"
          label="Spellcheck"
        />
        <!-- <Switch v-model="settings.docSize" label="Highlight Check" /> -->
        <Switch
          v-model="settings.docWidth"
          label="Full Width"
        />
        <span class="font-medium text-ink-gray-7 text-base my-2.5 px-2.5">
          Default Font
        </span>
        <div class="w-full flex justify-between gap-1 px-3">
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
      <div
        v-if="tab === 3"
        class="px-5 py-4 border-b"
      >
        <span
          class="inline-flex items-center gap-2.5 mb-5 text-ink-gray-8 font-medium text-lg w-full"
        >
          Transform
        </span>
        <div>
          <span
            v-if="$route.meta.documentPage && $store.state.hasWriteAccess"
            class="font-medium text-ink-gray-7 text-base"
          >
            Import
          </span>
          <Button
            v-if="$route.meta.documentPage && $store.state.hasWriteAccess"
            class="w-full justify-start mb-2"
            @click="() => emitter.emit('importDocFromWord')"
          >
            <template #prefix>
              <FileUp class="text-ink-gray-7 w-4 stroke-[1.5]" />
              Import DOCX
            </template>
          </Button>
          <span class="font-medium text-ink-gray-7 text-base">Export</span>
          <Button
            class="w-full justify-start"
            @click="() => emitter.emit('printFile')"
          >
            <template #prefix>
              <FileDown class="text-ink-gray-7 w-4 stroke-[1.5]" />
              Export PDF
            </template>
          </Button>
          <Button
            class="w-full justify-start"
            @click="() => $resources.exportMedia.submit()"
          >
            <template #prefix>
              <LucideImage class="text-ink-gray-7 w-4 stroke-[1.5]" />
              Export Media
            </template>
          </Button>
          <!-- <Button class="w-full justify-start">
            <template #prefix>
              <FileDown class="text-ink-gray-7 w-4" />
              Export to DOCX
            </template>
          </Button> -->
        </div>
      </div>
    </div>
  </div>
  <div
    class="hidden sm:flex flex-col items-center overflow-hidden h-full min-w-[48px] gap-1 pt-3 px-0 border-l z-0 bg-surface-white"
  >
    <template
      v-for="(item, index) in tabs"
      :key="item.label"
    >
      <button
        v-if="item.write === $store.state.hasWriteAccess || !item.write"
        variant="'ghost'"
        :class="[
          tab === index && showInfoSidebar
            ? 'text-black bg-surface-gray-3'
            : ' hover:bg-surface-menu-bar',
        ]"
        class="h-7 w-7 text-ink-gray-5 rounded"
        @click="switchTab(index)"
      >
        <component
          :is="item.icon"
          :class="[
            tab === 1 && showInfoSidebar
              ? 'text-ink-gray-7'
              : 'text-ink-gray-5',
          ]"
          class="mx-auto stroke-[1.5] text-ink-gray-5 size-4"
        />
      </button>
    </template>
    <!-- 
      Might spawn from emits 
      so they fall outside of tabs scope
    -->
    <InsertImage
      v-model="addImageDialog"
      :editor="editor"
    />
    <InsertVideo
      v-model="addVideoDialog"
      :editor="editor"
    />
    <NewManualSnapshotDialog
      v-if="newSnapshotDialog"
      v-model="newSnapshotDialog"
      @success="
        (data) => {
          storeSnapshot(data)
        }
      "
    />
    <SnapshotPreviewDialog
      v-if="snapShotDialog"
      v-model="snapShotDialog"
      :snapshot-data="selectedSnapshot"
      @success="
        (data) => {
          applySnapshot(selectedSnapshot)
        }
      "
    />
  </div>
</template>

<script>
import { Avatar, Input, Popover, Badge, Dropdown, Switch } from "frappe-ui"
import TagInput from "@/components/TagInput.vue"
import Tag from "@/components/Tag.vue"
import { getIconUrl } from "@/utils/getIconUrl"
import { v4 as uuidv4 } from "uuid"
import { defineAsyncComponent, markRaw } from "vue"
import OuterCommentVue from "@/components/DocEditor/components/OuterComment.vue"
import LineHeight from "../icons/line-height.vue"
import { entitiesDownload } from "@/utils/download"

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
  MessageCircle,
  FileText,
  FileClock,
  LucideInfo,
  Code,
  Code2,
  Table2Icon,
  LucideClock,
} from "lucide-vue-next"

import "@fontsource/lora"
import "@fontsource/geist-mono"
import "@fontsource/nunito"
import ColorInput from "../components/ColorInput.vue"
import Bold from "../icons/Bold.vue"
import Strikethrough from "../icons/StrikeThrough.vue"
import Underline from "../icons/Underline.vue"
import GeneralAccess from "@/components/GeneralAccess.vue"
import Indent from "../icons/Indent.vue"
import Outdent from "../icons/Outdent.vue"
import Codeblock from "../icons/Codeblock.vue"
import List from "../icons/List.vue"
import OrderList from "../icons/OrderList.vue"
import Check from "../icons/Check.vue"
import Details from "../icons/Details.vue"
import alignRight from "../icons/AlignRight.vue"
import alignLeft from "../icons/AlignLeft.vue"
import alignCenter from "../icons/AlignCenter.vue"
import alignJustify from "../icons/AlignJustify.vue"
import BlockQuote from "../icons/BlockQuote.vue"
import Style from "../icons/Style.vue"
import Image from "../icons/Image.vue"
import Video from "../icons/Video.vue"
import { useTimeAgo } from "@vueuse/core"
import * as Y from "yjs"
import { TiptapTransformer } from "@hocuspocus/transformer"
import { fromUint8Array, toUint8Array } from "js-base64"
import { formatDate, formatSize } from "@/utils/format"
import AnnotationList from "../components/AnnotationList.vue"
import ActivityTree from "../../ActivityTree.vue"
import { generalAccess, userList } from "@/resources/permissions"

export default {
  name: "DocMenuAndInfoBar",
  components: {
    Switch,
    Input,
    Avatar,
    TagInput,
    Tag,
    OuterCommentVue,
    Popover,
    InsertImage: defineAsyncComponent(() => import("./InsertImage.vue")),
    InsertVideo: defineAsyncComponent(() => import("./InsertVideo.vue")),
    SnapshotPreviewDialog: defineAsyncComponent(() =>
      import("./SnapshotPreviewDialog.vue")
    ),
    NewManualSnapshotDialog: defineAsyncComponent(() =>
      import("./NewManualSnapshotDialog.vue")
    ),
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
    TextQuote,
    MessageCircle,
    FileText,
    Details,
    GeneralAccess,
    AnnotationList,
    ActivityTree,
  },
  inject: ["editor", "document"],
  inheritAttrs: false,
  props: {
    settings: {
      type: Object,
      required: true,
    },
    allAnnotations: {
      type: Object,
      required: true,
    },
    activeAnnotation: {
      type: String,
      required: false,
    },
  },
  emits: ["update:allComments", "update:activeAnnotation"],
  setup() {
    return { getIconUrl }
  },
  data() {
    return {
      generalAccess: generalAccess.data,
      sharedWithList: userList.data,
      tab: this.entity?.write ? 0 : 4,
      formatDate,
      formatSize,
      docFont: this.settings.docFont,
      tabs: [
        {
          name: "Typography",
          icon: markRaw(Style),
          write: true,
        },
        {
          name: "Insert",
          icon: markRaw(Plus),
          write: true,
        },
        {
          name: "Document Settings",
          icon: markRaw(FileText),
          write: true,
        },
        {
          name: "Transforms",
          icon: markRaw(ArrowDownUp),
          write: false,
        },
        {
          name: "Information",
          icon: markRaw(LucideInfo),
          write: false,
        },
        {
          name: "Versions",
          icon: markRaw(FileClock),
          write: false,
          disabled: this.$store.state.activeEntity.write === 0,
        },
        {
          name: "Clock",
          icon: markRaw(LucideClock),
          write: false,
          disabled: this.$store.state.user.id === "Guest",
        },
      ].filter((item) => !item.disabled),
      newComment: "",
      showShareDialog: false,
      addImageDialog: false,
      addVideoDialog: false,
      addTag: false,
      snapShotDialog: false,
      selectedSnapshot: null,
      stagedSnapshot: null,
      newSnapshotDialog: false,
    }
  },
  computed: {
    userId() {
      return this.$store.state.user.id
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
      return this.$store.state.activeEntity
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
      } else if (this.entity.comment) {
        return true
      } else {
        return false
      }
    },
    showActivity() {
      if (this.userId === "Guest") return
      else if (this.entity.owner === "You") {
        return true
      } else if (this.entity.owner.value.write) {
        return true
      }
      return false
    },
  },
  mounted() {
    this.emitter.on("addImage", () => {
      this.addImageDialog = true
    })
    this.emitter.on("addVideo", () => {
      this.addVideoDialog = true
    })
    // document.vue debouncedWatch
    this.emitter.on("triggerAutoSnapshot", () => {
      this.autoSnapshot()
    })
  },
  beforeUnmount() {
    this.emitter.off("triggerAutoSnapshot")
  },
  methods: {
    setActiveAnnotation(val) {
      this.$emit("update:activeAnnotation", val.get("id"))
      // focus the comment inside the editor. needs further testing
      /*       let from = val.rangeStart
      let to = val.rangeEnd
      //const { node } = this.editor.view.domAtPos(this.editor.state.selection.anchor);
      //if (node) {
        // Use node.parentElement if domAtPos returns text node instead of a DOM element
      //  (node.parentElement || node).scrollIntoView({ behavior: 'smooth'})
        // scrollIntoView(false); false == dont focus ediotr 
      //}
      //focusCommentWithActiveId(activeCommentId)
      //focusContentWithActiveId(activeCommentId) */
    },
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
    /* 
      Imperative that we take the snapshot EXACTLY when the user clicks `New`
      document state can change, so the sooner the better
    */
    autoSnapshot() {
      this.stagedSnapshot = Y.snapshot(this.document)
      this.$resources.storeVersion.submit({
        entity_name: this.entity.name,
        doc_name: this.entity.document,
        snapshot_message: `Auto generated version by ${this.currentUserName}`,
        snapshot_data: fromUint8Array(Y.encodeSnapshot(this.stagedSnapshot)),
      })
    },
    generateSnapshot() {
      this.newSnapshotDialog = true
      this.stagedSnapshot = Y.snapshot(this.document)
    },
    storeSnapshot(message) {
      this.$resources.storeVersion.submit({
        entity_name: this.entity.name,
        doc_name: this.entity.document,
        snapshot_message: message,
        snapshot_data: fromUint8Array(Y.encodeSnapshot(this.stagedSnapshot)),
      })
    },
    previewSnapshot(index) {
      let tempSnapshot = Y.decodeSnapshot(
        this.$resources.getversionList.data[index].snapshot_data
      )
      let tempDoc = Y.createDocFromSnapshot(
        this.document,
        tempSnapshot,
        new Y.Doc({ gc: false })
      )
      this.selectedSnapshot = Object.assign(
        {},
        this.$resources.getversionList.data[index]
      )
      this.selectedSnapshot.snapshot_data = tempDoc
      this.snapShotDialog = true
    },
    applySnapshot(data) {
      /* Simply generate the old snapshot state and write the new content */
      const snapshotDoc = data.snapshot_data
      const prosemirrorJSON = TiptapTransformer.fromYdoc(snapshotDoc).default // default pm fragment
      // setContent is a transactional dispatch
      // wipes `lastSaved` maybe
      this.editor.commands.setContent(prosemirrorJSON, true)
      this.$realtime.emit(
        "document_version_change_emit",
        "Drive File",
        this.entity.name,
        this.currentUserName,
        this.currentUserImage,
        this.$realtime.socket.id
      )
    },
    revertState(data) {
      // DO NOT USE
      // find a way to reset the cursor position of all connected clients
      const snapshotDoc = new Y.Doc({ gc: false })
      Y.applyUpdate(snapshotDoc, Y.encodeStateAsUpdate(data.snapshot_data))
      // state vectors
      const currentStateVector = Y.encodeStateVector(this.document)
      const snapshotStateVector = Y.encodeStateVector(snapshotDoc)

      // pack all changes from snapshot till now
      const changesSinceSnapshotUpdate = Y.encodeStateAsUpdate(
        this.document,
        snapshotStateVector
      )

      // apply them
      const um = new Y.UndoManager(snapshotDoc.getXmlFragment("default")) // prosemirror default fragment
      Y.applyUpdate(snapshotDoc, changesSinceSnapshotUpdate)

      // revert  them
      um.undo()

      // apply the revert operation
      const revertChangesSinceSnapshotUpdate = Y.encodeStateAsUpdate(
        snapshotDoc,
        currentStateVector
      )
      // propagate changes
      Y.applyUpdate(this.document, revertChangesSinceSnapshotUpdate)
    },
  },
  resources: {
    exportMedia() {
      return {
        url: "drive.api.files.export_media",
        params: {
          entity_name: this.entity.name,
        },
        auto: false,
        onSuccess(data) {
          entitiesDownload(null, data)
        },
      }
    },
    storeVersion() {
      return {
        url: "drive.api.files.create_doc_version",
        method: "POST",
        debounce: 1000,
        auto: false,
        onSuccess() {
          this.stagedSnapshot = null
          this.$resources.getversionList.fetch()
        },
      }
    },
    getversionList() {
      return {
        url: "drive.api.files.get_doc_version_list",
        method: "GET",
        params: {
          entity_name: this.entity.name,
        },
        auto: this.entity.write === 1 && this.tab === 6,
        onSuccess(data) {
          data.forEach((element) => {
            element.relativeTime = useTimeAgo(element.creation)
            element.creation = formatDate(element.creation)
            element.modified = formatDate(element.modified)
            element.snapshot_data = toUint8Array(element.snapshot_data)
          })
        },
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
        auto: this.userId !== "Guest",
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
