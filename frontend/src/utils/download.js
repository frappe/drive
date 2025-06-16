import JSZip from "jszip"
import { toast } from "./toasts"
import { printDoc } from "./files"
import html2pdf from "html2pdf.js"
import editorStyle from "@/components/DocEditor/editor.css?inline"
import globalStyle from "@/index.css?inline"

async function getPdfFromDoc(entity_name) {
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${entity_name}`
  )
  const raw_html = (await res.json()).message
  const content = `
          <!DOCTYPE html>
          <html>
            <head>
              <style>${globalStyle}</style>
              <style>${editorStyle}</style>
            </head>
            <body>
              <div class="Prosemirror prose-sm" style='padding-left: 40px; padding-right: 40px; padding-top: 20px; padding-bottom: 20px; margin: 0;'>
                ${raw_html}
              </div>
            </body>
          </html>
        `

  const pdfBlob = html2pdf().from(content).toPdf()
  await pdfBlob
  return pdfBlob.prop.pdf.output("arraybuffer")
}
export function entitiesDownload(team, entities) {
  if (entities.length === 1) {
    if (entities[0].mime_type === "frappe_doc") {
      return fetch(
        `/api/method/drive.api.files.get_file_content?entity_name=${entities[0].name}`
      ).then(async (data) => {
        const raw_html = (await data.json()).message
        printDoc(raw_html)
      })
    }
    return entities[0].is_group
      ? folderDownload(team, entities[0])
      : (window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${entities[0].name}&trigger_download=1`)
  }

  const t = toast("Preparing download...")
  const zip = new JSZip()

  const processEntity = async (entity, parentFolder) => {
    if (entity.is_group) {
      const folder = parentFolder.folder(entity.title)
      return get_children(team, entity.name).then((children) => {
        const promises = children.map((childEntity) =>
          processEntity(childEntity, folder)
        )
        return Promise.all(promises)
      })
    } else if (entity.document) {
      const content = await getPdfFromDoc(entities[0].name)
      parentFolder.file(entity.title + ".pdf", content)
    } else {
      const fileContent = await get_file_content(entity.name)
      parentFolder.file(entity.title, fileContent)
    }
  }

  const promises = entities.map((entity) => processEntity(entity, zip))

  Promise.all(promises)
    .then(() => {
      return zip.generateAsync({ type: "blob", streamFiles: true })
    })
    .then(async function (content) {
      var downloadLink = document.createElement("a")
      downloadLink.href = URL.createObjectURL(content)
      downloadLink.download = "Drive Download " + +new Date() + ".zip"

      document.body.appendChild(downloadLink)

      downloadLink.click()
      document.body.removeChild(downloadLink)
      document.getElementById(t).remove()
    })
    .catch(console.error)
}

export function folderDownload(team, root_entity) {
  const folderName = root_entity.title
  const zip = new JSZip()
  const rootFolder = zip.folder(root_entity.title)
  temp(team, root_entity.name, rootFolder)
    .then(() => {
      return zip.generateAsync({ type: "blob", streamFiles: true })
    })
    .then((content) => {
      const downloadLink = document.createElement("a")
      downloadLink.href = URL.createObjectURL(content)
      downloadLink.download = folderName + ".zip"

      document.body.appendChild(downloadLink)
      downloadLink.click()
      document.body.removeChild(downloadLink)
    })
    .catch((error) => {
      console.error(error)
    })
}

function temp(team, entity_name, parentZip) {
  return new Promise((resolve, reject) => {
    get_children(team, entity_name)
      .then((result) => {
        const promises = result.map((entity) => {
          if (entity.is_group) {
            const folder = parentZip.folder(entity.title)
            return temp(team, entity.name, folder)
          }
          if (entity.document) {
            getPdfFromDoc(entity.name).then((content) =>
              parentZip.file(entity.title + ".pdf", content)
            )
          } else {
            return get_file_content(entity.name).then((fileContent) => {
              parentZip.file(entity.title, fileContent)
            })
          }
        })

        Promise.all(promises)
          .then(() => {
            resolve()
          })
          .catch((error) => {
            reject(error)
          })
      })
      .catch((error) => {
        reject(error)
      })
  })
}

function get_file_content(entity_name) {
  const fileUrl =
    "/api/method/" +
    `drive.api.files.get_file_content?entity_name=${entity_name}`

  return fetch(fileUrl).then((response) => {
    if (response.ok) {
      return response.blob()
    } else if (response.status === 204) {
      console.log(response)
    } else {
      throw new Error(`Request failed with status ${response.status}`)
    }
  })
}

function get_children(team, entity_name) {
  const url =
    "/api/method/" +
    `drive.api.list.files?team=${team}&entity_name=${entity_name}`
  return fetch(url, {
    method: "GET",
    headers: {
      "X-Frappe-CSRF-Token": window.csrf_token,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }
      return response.json()
    })
    .then((json) => json.message)
}
