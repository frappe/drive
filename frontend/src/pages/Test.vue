<template>
  <div>
    <Dropdown
      placement="center"
      :options="[
        {
          icon: 'user',
          label: 'My Profile',
        },
        {
          icon: 'folder-minus',
          label: 'Archived Teams',
        },
        {
          icon: 'log-out',
          label: 'Log out',
        },
      ]"
    >
      <template #default="{ open }">
        <Button :class="open ? 'bg-gray-300' : 'hover:bg-gray-200'">
          Drop
        </Button>
      </template>
    </Dropdown>

    <Popover>
      <template #target="{ togglePopover }">
        <Button @click="togglePopover()">Pop</Button>
      </template>
      <template #body-main="{ togglePopover }">
        <div v-for="item in ['yes', 'no']" :key="item">
          <div
            @click="
              () => {
                togglePopover()
              }
            "
          >
            {{ item }}
          </div>
        </div>
      </template>
    </Popover>
  </div>
</template>

<script>
import { Popover, Button, Dropdown } from "frappe-ui"

export default {
  name: "Test",
  components: { Popover, Button, Dropdown },
}
</script>
