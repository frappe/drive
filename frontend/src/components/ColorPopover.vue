<template>
  <Popover trigger="hover" :hoverDelay="0.5" :leaveDelay="0.5">
    <template #target>
      <Button>Hover me</Button>
    </template>
    <template #body-main>
      <div class="p-2 text-base">Popup content</div>
    </template>
  </Popover>
</template>

<script>
import { Popover, Button } from 'frappe-ui';

export default {
  name: 'ColorPopover',
  components: { Popover, Button },
};
</script>
