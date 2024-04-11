let drive_collaboration_handlers = (socket, realtime) => {
  socket.on("send-update", (update) => {
    console.log(update);
    socket.broadcast.emit("sync-update", update);
  });
};

module.exports = drive_collaboration_handlers;
