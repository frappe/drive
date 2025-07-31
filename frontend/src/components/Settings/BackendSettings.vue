<template>
  <div class="flex items-center mb-4">
    <div>
      <h1 class="font-semibold text-ink-gray-9">
        {{ __("Backend") }}
      </h1>
      <p class="text-sm text-ink-gray-6">
        These are Drive-level settings. Handle with care.
      </p>
    </div>
    <Button
      label="Sync"
      @click="syncFromDisk"
      class="ml-auto mr-4"
    />
  </div>

  <div class="flex flex-col gap-4 pb-10">
    <FormControl
      type="select"
      label="Root Folder Type"
      :options="[
        { label: 'Team ID', value: 'team_id' },
        { label: 'Team Name', value: 'team_name' },
        { label: 'Other', value: 'other' },
      ]"
      v-model="generalSettings.rootPrefix"
      description="The root folder name for each team, defaults to team ID."
    />
    <FormControl
      v-if="generalSettings.rootPrefix === 'other'"
      label="Root Folder Name"
      placeholder="team"
      v-model="generalSettings.rootPrefixValue"
      description="Value to use for the root folder. Use / to not use a separate folder."
    />
    <FormControl
      label="Team Prefix"
      placeholder="team"
      v-model="generalSettings.teamPrefix"
      description="Team files will be placed inside this folder. Use / to place directly in the root folder."
    />
    <FormControl
      label="Personal Prefix"
      placeholder="personal"
      v-model="generalSettings.personalPrefix"
      description="Personal folders will be created under this prefix."
    />
    <FormControl
      type="select"
      label="Backend Type"
      :options="[
        { label: 'Disk', value: 'disk' },
        { label: 'S3', value: 's3' },
      ]"
      v-model="generalSettings.backendType"
    />
    <Button
      label="Update"
      variant="solid"
      :disabled="!edited"
      @click="saveS3Settings"
      class="mt-4"
    />
    <div
      v-if="backendType === 's3'"
      class="flex flex-col gap-2 mt-2"
    >
      <h3 class="font-semibold text-md">S3 Settings</h3>
      <FormControl
        label="AWS Key"
        placeholder="Enter AWS Key"
        v-model="s3Settings.awsKey"
      />
      <FormControl
        label="AWS Secret"
        placeholder="Enter AWS Secret"
        v-model="s3Settings.awsSecret"
        type="password"
      />
      <FormControl
        required
        label="S3 Bucket"
        placeholder="bucket.example"
        v-model="s3Settings.bucket"
      />
      <FormControl
        label="Endpoint URL"
        placeholder="Enter Endpoint URL"
        v-model="s3Settings.endpointUrl"
        description="Optional, only if using a custom endpoint."
      />
      <FormControl
        label="Signature Version"
        placeholder="s3v4"
        v-model="s3Settings.signatureVersion"
        description="Optional. Some providers only support 's3'."
      />
      <Button
        label="Save S3 Settings"
        variant="solid"
        :disabled="!subEdited"
        @click="saveS3Settings"
        class="mt-4"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from "vue"
import { FormControl, Button, confirmDialog, createResource } from "frappe-ui"
import { toast } from "@/utils/toasts"
import { root } from "postcss"

const edited = ref(false)
// used for sub-settings, e.g. S3
const subEdited = ref(false)

const generalSettings = reactive({
  rootPrefix: "team_id",
  rootPrefixValue: "",
  teamPrefix: "",
  personalPrefix: "",
  backendType: "disk",
})
const s3Settings = reactive({
  awsKey: "",
  awsSecret: "",
  bucket: "",
  endpointUrl: "",
  signatureVersion: "",
})

watch(generalSettings, () => (edited.value = true), { deep: true })

watch(s3Settings, () => (subEdited.value = true), { deep: true })

function syncFromDisk() {
  confirmDialog("Are you sure?")
}

const s3resource = createResource({
  url: "drive.api.product.update_s3_settings",
  makeParams: () => s3Settings,
  onSuccess() {
    subEdited.value = false
    toast({
      message: "S3 settings updated successfully",
      variant: "success",
    })
  },
})
async function saveS3Settings() {
  await s3resource.submit()
}
</script>
