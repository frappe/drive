import { Extension } from "@tiptap/core"
function extractEntityName(url) {
  try {
    const query = url.split("?")[1]
    if (!query) return null
    const params = new URLSearchParams(query)
    return params.get("embed_name")
  } catch {
    return null
  }
}

export default Extension.create({
  name: "embedCollector",
  addCommands() {
    return {
      getEmbedUrls:
        () =>
        ({ state }) => {
          const results = []
          let currentHeading = null
          let currentHeadingCount = 0

          state.doc.descendants((node) => {
            // If it's a heading, remember its text
            if (node.type.name === "heading") {
              currentHeadingCount = 0
              currentHeading = node.textContent.trim()
            }

            // If it's an image, pair it with the last heading
            if (
              (node.type.name === "image" || node.type.name === "video") &&
              node.attrs.src
            ) {
              results.push({
                title:
                  currentHeading +
                  (currentHeadingCount ? ` (${currentHeadingCount})` : ""),
                name: extractEntityName(node.attrs.src),
              })
              currentHeadingCount++
            }
          })

          return results
        },
    }
  },
})
