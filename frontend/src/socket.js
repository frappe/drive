import { io } from "socket.io-client"
import { socketio_port } from "../../../../sites/common_site_config.json"
export function initSocket() {
  let siteName = window.site_name || "drive.localhost"

  let default_port = window.socketio_port || socketio_port || "9000"
  let port = window.location.port ? `:${default_port}` : ""
  let protocol = port ? "http" : "https"
  let host = window.location.hostname

  let url = `${protocol}://${host}${port}/${siteName}`
  let socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  })
  socket.on("connect_error", (data) => {
    console.log(data)
  })
  return socket
}
