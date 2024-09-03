// same room evals as frappe
const doc_room = (doctype, docname) => "doc:" + doctype + "/" + docname;
const open_doc_room = (doctype, docname) =>
  "open_doc:" + doctype + "/" + docname;
const doctype_room = (doctype) => "doctype:" + doctype;
const task_room = (task_id) => "task_progress:" + task_id;
const user_room = (user) => "user:" + user;

let drive_handlers = (socket) => {
  socket.on(
    "document_version_change_emit",
    (doctype, document, user, user_image, clientID) => {
      let room = doc_room(doctype, document);
      socket.nsp.to(room).emit("document_version_change_recv", {
        doctype: doctype,
        docname: document,
        author: user,
        author_image: user_image,
        author_id: clientID,
      });
    }
  );
};

module.exports = drive_handlers;
