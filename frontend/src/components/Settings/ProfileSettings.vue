<template>
  <h1 class="font-semibold mb-8 text-ink-gray-9">
    {{ __("Profile") }}
  </h1>
  <div class="flex justify-start w-full items-center gap-x-4">
    <Avatar
      :image="newImageUrl"
      size="3xl"
      :label="fullName"
      class="w-20 h-20"
    />
    <div class="flex flex-col">
      <span class="text-xl font-semibold text-ink-gray-8">{{ fullName }}</span>
      <span class="text-base text-ink-gray-6">{{ $store.state.user.id }}</span>
    </div>
    <Button
      class="ml-auto"
      @click="editProfileDialog = true"
    >
      {{ __("Edit profile") }}
    </Button>
  </div>
  <Dialog
    v-model="editProfileDialog"
    :options="{
      title: __('Edit Profile'),
      size: 'md',
      actions: [
        {
          label: __('Confirm'),
          variant: 'solid',
          onClick: updateProfile,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col items-start justify-start gap-y-2">
        <span class="text-base text-ink-gray-5">Profile Photo</span>
        <div class="flex items-center justify-between w-full">
          <Avatar
            :image="newImageUrl"
            size="3xl"
            :label="newFullName"
            class="w-20 h-20"
          />

          <div
            v-if="newImageUrl"
            class="flex items-center justify-between bg-surface-gray-2 h-7 pl-2 text-base rounded"
          >
            <LucideLink class="mr-2" />
            <a
              :href="newImageUrl"
              class="truncate max-w-56 underline"
              >{{ newImageUrl }}</a
            >

            <Button @click="newImageUrl = null">
              <template #icon>
                <LucideX class="stroke-1 h-4" />
              </template>
            </Button>
          </div>
          <FileUploader
            v-else
            file-types="image/png, image/jpeg, image/jpg"
            :validate-file="validateFile"
            @success="
              (file) => {
                console.log(file)
                newImageUrl = file.file_url
              }
            "
          >
            <template #default="{ openFileSelector }">
              <Button @click="openFileSelector">
                {{ __("Add Image") }}
              </Button>
            </template>
          </FileUploader>
        </div>
        <div class="w-full flex flex-col gap-y-2 my-2">
          <span class="text-base text-ink-gray-5">{{ __("First Name") }}</span>
          <Input
            v-model="newFirstName"
            v-focus
          />
          <span class="text-base text-ink-gray-5">{{ __("Last Name") }}</span>
          <Input v-model="newLastName" />
        </div>
      </div>
    </template>
  </Dialog>
  <h1 class="font-semibold mt-12 mb-4 text-ink-gray-8">
    {{ __("Preferences") }}
  </h1>
  <Autocomplete
    v-model="defaultTeam"
    placeholder="Not set"
    :options="teamOptions"
    label="Default Team"
    class="mb-3"
  />
  <Switch
    v-model="singleClick"
    label="Single click to open files and folders"
    class="!px-0 hover:!bg-inherit"
  />
  <Switch
    v-model="detectLinks"
    label="Automatically detect links"
    class="!px-0 hover:!bg-inherit"
  />
</template>
<script setup>
import {
  Button,
  Input,
  Avatar,
  Dialog,
  FileUploader,
  Switch,
  Autocomplete,
  createDocumentResource,
} from "frappe-ui"
import LucideLink from "~icons/lucide/link"
import LucideX from "~icons/lucide/x"

import { useStore } from "vuex"
import { ref, computed, watch } from "vue"
import { getTeams } from "@/resources/files"
import { settings, setSettings } from "@/resources/permissions"

const store = useStore()

const newImageUrl = ref(store.state.user.imageURL)
const fullName = computed(() => store.state.user.fullName)
const newLastName = ref(fullName.value.split(" ")[1])
const newFirstName = ref(fullName.value.split(" ")[0])
const newFullName = computed(() => newFirstName.value + " " + newLastName.value)

const editProfileDialog = ref(false)

const teamOptions = computed(() =>
  Object.keys(getTeams.data).map((k) => ({
    value: k,
    label: getTeams.data[k].title,
  }))
)
const singleClick = ref(Boolean(settings.data.single_click))
const detectLinks = ref(Boolean(settings.data.auto_detect_links))
const defaultTeam = ref(settings.data.default_team || { label: "-" })
const options = {
  single_click: singleClick,
  auto_detect_links: detectLinks,
  default_team: defaultTeam,
}
for (let k in options) {
  watch(options[k], (v) => {
    setSettings.submit({
      updates: { [k]: v },
    })
  })
}

const profile = createDocumentResource({
  doctype: "User",
  name: store.state.user.id,
  auto: true,
})

const updateProfile = () => {
  profile.setValue
    .submit({
      first_name: newFirstName.value,
      last_name: newLastName.value,
      user_image: newImageUrl.value,
    })
    .then((data) => {
      store.state.user.fullName = data.full_name
      store.state.user.imageURL = data.user_image
      editProfileDialog.value = false
    })
}

const validateFile = (file) => {
  let extension = file.name.split(".").pop().toLowerCase()
  if (!["jpg", "jpeg", "png"].includes(extension)) {
    alert("Not a valid Image file")
    return false
  }
}
</script>
