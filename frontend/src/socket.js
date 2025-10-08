import { io } from "socket.io-client"

export async function initSocket() {
  let socketio_port = "9000"
  let siteName = window.site_name

  if (import.meta.env.DEV) {
    try {
      const cfg = await import("../../../../sites/common_site_config.json", {
        assert: { type: "json" },
      })
      socketio_port = cfg.socketio_port
      siteName = cfg.default_site
    } catch {
      console.log("You have not set a default site, sockets won't work in dev.")
    }
  }

  let port = window.location.port
    ? `:${window.socketio_port || socketio_port}`
    : ""
  let protocol = port ? "http" : "https"
  let host = window.location.hostname

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
