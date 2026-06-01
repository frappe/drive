import JSZip from 'jszip'
import { toast } from './toasts'

export function entitiesDownload(team, entities) {
  if (entities.length === 1) {
    return entities[0].is_folder
      ? folderDownload(team, entities[0])
      : (window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${entities[0].name}&trigger_download=1`)
  }

  const t = toast('Preparing download...')
  const zip = new JSZip()

  const processEntity = async (entity, parentFolder) => {
    if (entity.is_folder) {
      const folder = parentFolder.folder(entity.file_name)
      return get_children(team, entity.name).then((children) => {
        const promises = children.map((childEntity) => processEntity(childEntity, folder))
        return Promise.all(promises)
      })
    } else if (entity.document) {
      return
    } else {
      const fileContent = await get_file_content(entity)
      parentFolder.file(entity.file_name, fileContent)
    }
  }

  const promises = entities.map((entity) => processEntity(entity, zip))

  Promise.all(promises)
    .then(() => {
      return zip.generateAsync({ type: 'blob', streamFiles: true })
    })
    .then(async function (content) {
      var downloadLink = document.createElement('a')
      downloadLink.href = URL.createObjectURL(content)
      downloadLink.download = 'Drive Download ' + +new Date() + '.zip'

      document.body.appendChild(downloadLink)

      downloadLink.click()
      document.body.removeChild(downloadLink)
      document.getElementById(t).remove()
    })
    .catch(console.error)
}

export function folderDownload(team, root_entity) {
  const folderName = root_entity.file_name
  const zip = new JSZip()
  const rootFolder = zip.folder(folderName)
  temp(team, root_entity.name, rootFolder)
    .then(() => {
      return zip.generateAsync({ type: 'blob', streamFiles: true })
    })
    .then((content) => {
      const downloadLink = document.createElement('a')
      downloadLink.href = URL.createObjectURL(content)
      downloadLink.download = folderName + '.zip'

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
          if (entity.is_folder) {
            const folder = parentZip.folder(entity.file_name)
            return temp(team, entity.name, folder)
          }
          if (entity.document) {
            return
          }
          return get_file_content(entity).then((fileContent) => {
            parentZip.file(entity.file_name, fileContent)
          })
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

function get_file_content(entity) {
  const fileUrl =
    entity.src ||
    '/api/method/' +
      `drive.api.files.get_file_content?entity_name=${entity.name}&trigger_download=1`

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
  const url = '/api/method/' + `drive.api.list.files?team=${team}&entity_name=${entity_name}`
  return fetch(url, {
    method: 'GET',
    headers: {
      'X-Frappe-CSRF-Token': window.csrf_token,
      'Content-Type': 'application/json',
      Accept: 'application/json',
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
