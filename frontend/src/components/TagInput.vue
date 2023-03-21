<template>
  <Popover transition="default" :show="hackyFlag && filteredTags.length">
    <template #target="{}">
      <Input
        v-model="tagInputText"
        v-focus
        v-on-outside-click="closeInput"
        type="text"
        class="h-6"
        @input="tagInputText = $event"
        @keydown.enter="
          (e) =>
            $resources.createTag.submit({
              title: e.target.value.trim(),
            })
        " />
    </template>

    <template #body-main="{}">
      <div class="p-1" @click.stop>
        <div v-for="tag in filteredTags" :key="tag.name">
          <div
            :class="`hover:bg-gray-100 cursor-pointer rounded-md py-1.5 px-2 text-gray-800 text-[12px]`"
            @click="
              $resources.addTag.submit({
                entity: entity.name,
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
  name: "TagInput",
  components: {
    Input,
    Popover,
  },

  props: {
    entity: {
      type: Object,
      required: true,
      default: null,
    },
    unaddedTags: {
      type: Array,
      required: true,
      default: null,
    },
  },

  emits: ["success", "close"],

  data() {
    return {
      tagInputText: "",
      hackyFlag: false, // temporary hacky flag to circumvent v-on-outside-click from running on mounting
    };
  },

  computed: {
    filteredTags() {
      return this.unaddedTags.filter((x) =>
        x.title.toLowerCase().startsWith(this.tagInputText.toLowerCase())
      );
    },
  },

  methods: {
    closeInput() {
      if (this.hackyFlag) this.$emit("close");
      this.hackyFlag = !this.hackyFlag;
    },
  },

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
