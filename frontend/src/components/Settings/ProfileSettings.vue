<template>
  <h1 class="font-semibold mb-8">Profile</h1>
  <div class="flex justify-start w-full items-center gap-x-4">
    <Avatar
      :image="newImageUrl"
      size="3xl"
      :label="fullName"
      class="w-20 h-20"
    />
    <div class="flex flex-col">
      <span class="text-xl font-semibold">{{ fullName }}</span>
      <span class="text-base text-gray-700">{{ currentUserEmail }}</span>
    </div>
    <Button class="ml-auto" @click="editProfileDialog = true"
      >Edit profile</Button
    >
  </div>
  <Dialog
    v-model="editProfileDialog"
    :options="{
      title: 'Edit Profile',
      size: 'md',
      actions: [
        {
          label: 'Confirm',
          variant: 'solid',
          onClick: updateProfile,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col items-start justify-start gap-y-2">
        <span class="text-base text-gray-600">Profile Photo</span>
        <div class="flex items-center justify-between w-full">
          <Avatar
            :image="newImageUrl"
            size="3xl"
            :label="newFullName"
            class="w-20 h-20"
          />

          <div
            v-if="newImageUrl"
            class="flex items-center justify-between bg-gray-100 h-7 pl-2 text-base rounded"
          >
            <Link class="mr-2" />
            <a :href="newImageUrl" class="truncate max-w-56 underline">{{
              newImageUrl
            }}</a>

            <Button @click="newImageUrl = null"
              ><template #icon> <X class="stroke-1 h-4" /> </template
            ></Button>
          </div>
          <FileUploader
            v-else
            :file-types="'image/png, image/jpeg, image/jpg'"
            :validate-file="validateFile"
            @success="
              (file) => {
                newImageUrl = file.file_url
              }
            "
          >
            <template #default="{ openFileSelector }">
              <Button @click="openFileSelector"> Add Image </Button>
            </template>
          </FileUploader>
        </div>
        <div class="w-full flex flex-col gap-y-2 my-2">
          <span class="text-base text-gray-600">First Name</span>
          <Input v-model="newFirstName"></Input>
          <span class="text-base text-gray-600">Last Name</span>
          <Input v-model="newLastName"></Input>
        </div>
      </div>
      <ErrorMessage
        v-if="errorMessage"
        class="text-sm mt-2"
        :message="errorMessage"
      />
    </template>
  </Dialog>
  <h1 class="font-semibold mt-12 mb-4">Preferences</h1>
  <Autocomplete :options="teamOptions" v-model="defaultTeam" label="Team" />
  <Switch
    v-model="singleClick"
    label="Single click to open files and folders"
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
  createResource,
} from "frappe-ui"
import Link from "../EspressoIcons/Link.vue"
import { X } from "lucide-vue-next"
import { useStore } from "vuex"
import { ref, computed, watch } from "vue"
import ErrorMessage from "frappe-ui/src/components/ErrorMessage.vue"
import { getTeams } from "@/resources/files"
import { settings, setSettings } from "@/resources/permissions"

const store = useStore()
const newImageUrl = ref(store.state.user.imageURL)
const newLastName = ref(store.state.user.fullName.split(" ")[1])
const newFirstName = ref(store.state.user.fullName.split(" ")[0])
const fullName = computed(() => store.state.user.fullName)
const newFullName = computed(() => this.newFirstName + " " + this.newLastName)
const editProfileDialog = ref(false)

const teamOptions = computed(() =>
  Object.keys(getTeams.data).map((k) => ({
    value: k,
    label: getTeams.data[k].title,
  }))
)
const singleClick = ref(Boolean(settings.data.message.single_click))
watch(singleClick, (v) => {
  setSettings.submit({ updates: { single_click: v } })
})
const defaultTeam = ref(settings.data.message.default_team)
watch(defaultTeam, (v) => {
  setSettings.submit({ updates: { default_team: v.value } })
})
// const profile = createResource({
//   type: "document",
//   doctype: "User",
//   name: store.state.user.id,
//   auto: true,
//   realtime: true,
// })

// const updateProfile = () => {
//   profile.setValue
//     .submit({
//       first_name: newFirstName.value,
//       last_name: newLastName.value,
//       user_image: newImageUrl.value,
//     })
//     .then((data) => {
//       store.state.user.fullName = data.full_name
//       store.state.user.imageURL = data.user_image
//       editProfileDialog.value = false
//     })
// }

const validateFile = (file) => {
  let extension = file.name.split(".").pop().toLowerCase()
  if (!["jpg", "jpeg", "png"].includes(extension)) {
    this.errorMessage = "Not a valid Image file"
  } else {
    this.errorMessage = null
  }
}
</script>
