import JSZip from 'jszip';

export function folderDownload(root_entity)
{

    var folderName = root_entity.title;

    var zip = new JSZip();

    temp(root_entity.name,zip);

    zip.generateAsync({ type: 'blob' })
      .then(function (content) {
        // Create a download link
        var downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(content);
        downloadLink.download = folderName + '.zip';

        // Append the link to the document body and trigger the download
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      });
}

function temp(entity_name,parentZip)
{
    let result = get_children(entity_name);
    result.forEach((entity) => {
        let current_entity = entity;
        console.log(current_entity.title);
        if (current_entity.is_group)
        {
           var folder = parentZip.folder(current_entity.title);
           temp(current_entity.name,folder);
        }
        else{
            console.log("sucess.....")
            parentZip.file(current_entity.title, get_file_content(current_entity.name));
            
        }
       
      });
}

function get_file_content(entity_name)
{
    var fileUrl = window.location.origin +
            "/api/method/" +
            `drive.api.files.get_file_content?entity_name=${entity_name}`;
            const xhr = new XMLHttpRequest();
            xhr.open("GET",fileUrl, false); // Here i am seeting third parameter as false for a synchronous request
            xhr.send();
          
            if (xhr.status === 200) {
              return xhr.response;
            } else {
              throw new Error(`Request failed with status ${xhr.status}`);
            }
}

function get_children(entity_name) {
    const url =
      window.location.origin +
      "/api/method/" +
      `drive.api.nested_folder.folder_contents?entity_name=${entity_name}`;
  
    const xhr = new XMLHttpRequest();
    xhr.open("GET", url, false); // Here i am seeting third parameter as false for a synchronous request
    xhr.send();
  
    if (xhr.status === 200) {
      const json = JSON.parse(xhr.responseText);
      return json.message;
    } else {
      throw new Error(`Request failed with status ${xhr.status}`);
    }
  }