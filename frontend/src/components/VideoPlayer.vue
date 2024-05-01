<template>
  <div>
    <video ref="videoPlayer" preload="auto"></video>
  </div>
</template>

<script>
import videojs from "video.js"
import "video.js/dist/video-js.min.css"

export default {
  name: "VideoPlayer",
  props: {
    options: {
      type: Object,
      default() {
        return {}
      },
    },
  },
  data() {
    return {
      player: null,
    }
  },
  mounted() {
    this.player = videojs(this.$refs.videoPlayer, this.options, () => {
      this.player.log("onPlayerReady", this)
      this.player.fluid(true)
    })
  },
  beforeUnmount() {
    if (this.player) {
      this.player.dispose()
    }
  },
}
</script>
