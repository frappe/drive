<template>
  <Popover transition="default">
    <template #target="{ open }">
      <Input
        type="text"
        class="h-6"
        @focus="open"
        v-on-outside-click="close"
        @keydown.enter="
          (e) =>
            $resources.createTag.submit({
              title: e.target.value.trim(),
            })
        " />
    </template>

    <template #body-main="{}">
      <div class="p-1" @click.stop>
        <div v-for="tag in unaddedTags" :key="tag.name">
          <div
            :class="`hover:bg-${tag.color}-100 cursor-pointer rounded-md py-1.5 px-2 text-${tag.color}-600 text-[12px]`"
            @click="
              $resources.addTag.submit({
                entity: this.entity.name,
                tag: tag.name,
              })
            ">
            {{ tag.title }}
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script>
import { Input, Popover } from "frappe-ui";

export default {
  name: "AddTagInput",
  components: {
    Input,
    Popover,
  },

  data() {
    return {
      hackyFlag: false, // temporary hacky flag to circumvent v-on-outside-click from running on mounting
    };
  },
  props: {
    entity: {
      type: Object,
      required: true,
    },
    unaddedTags: {
      type: Array,
      required: true,
    },
  },

  methods: {
    close() {
      if (this.hackyFlag) this.$emit("close");
      this.hackyFlag = !this.hackyFlag;
    },
  },

  emits: ["success", "close"],

  resources: {
    createTag() {
      return {
        url: "drive.api.tags.create_tag",
        onSuccess(data) {
          this.$resources.addTag.submit({
            entity: this.entity.name,
            tag: data,
          });
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
    addTag() {
      return {
        url: "drive.api.tags.add_tag",
        onSuccess() {
          this.$emit("success");
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
  },
};
</script>
