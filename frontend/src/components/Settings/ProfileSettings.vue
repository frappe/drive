<template>
  <h1 class="font-semibold mb-8">Profile</h1>
  <div class="flex justify-start w-full items-center gap-x-4">
    <Avatar :image="imageURL" size="3xl" :label="fullName" class="w-20 h-20" />
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
          onClick: submit,
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
            <template
              #default="{ file, progress, uploading, openFileSelector }"
            >
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
  <!-- 
    Prefs 
      Folders before files
      Custom time locale
      Relative time toggle
  -->
</template>
<script>
import { Button, Input, Avatar, Dialog, FileUploader } from "frappe-ui"
import Link from "../EspressoIcons/Link.vue"
import { X } from "lucide-vue-next"
import ErrorMessage from "frappe-ui/src/components/ErrorMessage.vue"

export default {
  name: "NoFilesSection",
  components: {
    Avatar,
    Button,
    Input,
    Dialog,
    Link,
    X,
    FileUploader,
    ErrorMessage,
  },
  data() {
    return {
      newImageUrl: this.$store.state.user.imageURL,
      newFirstName: this.$store.state.user.fullName.split(" ")[0],
      newLastName: this.$store.state.user.fullName.split(" ")[1],
      editProfileDialog: false,
      addImageDialog: true,
      errorMessage: null,
      routeOptions: [
        {
          group: "Routes",
          hideLabel: true,
          items: [
            {
              icon: "home",
              label: "Home",
            },
            {
              icon: "clock",
              label: "Recents",
            },
            {
              icon: "star",
              label: "Favourites",
            },
            {
              icon: "users",
              label: "Shared",
            },
            {
              icon: "trash-2",
              label: "Trash",
            },
          ],
        },
      ],
    }
  },
  computed: {
    newFullName() {
      return this.newFirstName + " " + this.newLastName
    },
    isExpanded() {
      return this.$store.state.IsSidebarExpanded
    },
    firstName() {
      return this.$store.state.user.fullName.split(" ")[0]
    },
    lastName() {
      return this.$store.state.user.fullName.split(" ")[1]
    },
    currentUserEmail() {
      return this.$store.state.auth.user_id
    },
    fullName() {
      return this.$store.state.user.fullName
    },
    imageURL() {
      return this.$store.state.user.imageURL
    },
  },
  methods: {
    submit() {
      this.$resources.profile.setValue
        .submit({
          first_name: this.newFirstName,
          last_name: this.newLastName,
          user_image: this.newImageUrl,
        })
        .then((data) => {
          this.$store.state.user.fullName = data.full_name
          this.$store.state.user.imageURL = data.user_image
          this.editProfileDialog = false
        })
    },
    validateFile(file) {
      let extension = file.name.split(".").pop().toLowerCase()
      if (!["jpg", "jpeg", "png"].includes(extension)) {
        this.errorMessage = "Not a valid Image file"
      } else {
        this.errorMessage = null
      }
    },
  },
  resources: {
    profile() {
      return {
        type: "document",
        doctype: "User",
        name: this.currentUserEmail,
        auto: true,
        realtime: true,
      }
    },
  },
}
</script>
