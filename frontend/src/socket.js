import { io } from "socket.io-client"
import {
  socketio_port,
  default_site,
} from "../../../../sites/common_site_config.json"

export function initSocket() {
  let host = window.location.hostname
  let siteName = import.meta.env.DEV ? default_site : window.site_name
  let port = window.location.port
    ? `:${window.socketio_port || socketio_port}`
    : ""
  let protocol = port ? "http" : "https"
  let url = `${protocol}://${host}${port}/${siteName}`
  console.log(url)
  let socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  })
  socket.on("connect_error", (data) => {
    console.log(data)
  })
  return socket
}
