import { io } from "socket.io-client"
import { socketio_port } from "../../../../sites/common_site_config.json"

export function initSocket() {
  let host = window.location.hostname
  let port = window.location.port ? `:${socketio_port}` : ""
  let protocol = port ? "http" : "https"
  let url = `${protocol}://${host}${port}/${host}`
  let socket = io(url, {
    port: port,
    path: host,
    withCredentials: true,
    reconnectionAttempts: 5,
  })
  socket.on("connect", () => {
    console.log("connected")
  })
  socket.on("disconnect", () => {
    console.log("disconnected")
  })

  socket.on("connect_error", (err) => {
    console.log(err.message)
  })

  return socket
}
