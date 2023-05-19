<template>
  <div class="px-4 bg-white">
    <Dropdown
      :options="[
        {
          group: 'New',
          hideLabel: true,
          items: [
            {
              label: 'New File',
              handler: () => alert('New File'),
            },
            {
              label: 'Open File',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
          ],
        },
        {
          group: 'Current File',
          hideLabel: true,
          items: [
            { label: 'Copy File', handler: () => alert('Open File') },
            { label: 'Share File', handler: () => alert('Open File') },
            { label: 'Add to favourites', handler: () => alert('Open File') },
          ],
        },
        {
          group: 'Delete',
          hideLabel: true,
          items: [{ label: 'Delete File' }],
        },
      ]">
      <template v-slot="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]">
          File
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'New',
          hideLabel: true,
          items: [
            {
              label: 'Undo',
              handler: () => alert('New File'),
            },
            {
              label: 'Redo',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Cut',
              handler: () => alert('New File'),
            },
            {
              label: 'Copy',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Paste',
              handler: () => alert('New File'),
            },
            {
              label: 'Paste without Formatting',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Select All',
              handler: () => alert('New File'),
            },
            {
              label: 'Find and Replace',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
          ],
        },
      ]">
      <template v-slot="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]">
          Edit
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'New',
          hideLabel: true,
          items: [
            {
              label: 'Mode',
              handler: () => alert('New File'),
            },
            {
              label: 'Text Width',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Focus Mode',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
            {
              label: 'Full screen',
              handler: () => alert('New Window'),
              // show/hide option based on condition function
              condition: () => true,
            },
          ],
        },
      ]">
      <template v-slot="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]">
          View
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'Insert',
          hideLabel: true,
          items: [
            {
              label: 'Image',
              handler: () => alert('New File'),
            },
            {
              label: 'Video',
              handler: () => alert('New File'),
            },
            {
              label: 'Table',
              handler: () => alert('New File'),
            },
            {
              label: 'Link',
              handler: () => alert('New File'),
            },
            {
              label: 'Horizontal Line',
              handler: () => alert('New File'),
            },
            {
              label: 'Emoji',
              handler: () => alert('New File'),
            },
            {
              label: 'Blockquote',
              handler: () => alert('New File'),
            },
          ],
        },
      ]">
      <template v-slot="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]">
          Insert
        </button>
      </template>
    </Dropdown>
    <Dropdown
      :options="[
        {
          group: 'New',
          hideLabel: true,
          items: [
            {
              label: 'Text',
              handler: () => alert('New File'),
            },
            {
              label: 'Style',
              handler: () => alert('New File'),
            },
            {
              label: 'Alignment',
              handler: () => alert('New File'),
            },
            {
              label: 'Line Height',
              handler: () => alert('New File'),
            },
            {
              label: 'Horizontal Line',
              handler: () => alert('New File'),
            },
            {
              label: 'List and Numbering',
              handler: () => alert('New File'),
            },
            {
              label: 'Table',
              handler: () => alert('New File'),
            },
          ],
        },
      ]">
      <template v-slot="{ open }">
        <button
          :class="[
            'rounded-md px-2 py-1 text-base font-medium',
            open ? 'bg-slate-100' : 'bg-white-200',
          ]">
          Format
        </button>
      </template>
    </Dropdown>
  </div>
</template>

<script>
import { Dropdown } from "frappe-ui";

export default {
  name: "MenuBar",
  components: {
    Dropdown,
  },
};
</script>
