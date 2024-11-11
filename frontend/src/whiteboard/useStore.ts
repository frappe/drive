import { createTLStore, TLAssetStore, uniqueId } from "tldraw"

const encodeFileToDataURL = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = (error) => reject(error)
  })

const assets: TLAssetStore = {
  async upload(_, file) {
    const objectName = `${uniqueId()}-${file.name}`
    const imagePath = `tldraw/assets/${encodeURIComponent(objectName)}`
    const encodedFile = await encodeFileToDataURL(file)

    return "/" + imagePath
  },

  resolve(asset) {
    return asset.props.src
  },
}

export function useStore() {
  return createTLStore()
}
