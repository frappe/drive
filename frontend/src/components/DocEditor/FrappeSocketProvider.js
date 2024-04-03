import * as Y from "yjs";
import { Observable } from "lib0/observable";
import * as bc from "lib0/broadcastchannel";

export class FrappeSocketProvider extends Observable {
  constructor(socket, entityID, document) {
    super();
    this.document = document;
    this.entityID = entityID;
    this.socket = socket;

    //bc.subscribe(this._broadcastChannel, this.onBroadcastChannelMessage)
    //bc.publish(this._broadcastChannel, {
    //  type: 'sync-update',
    //  data: update
    //}, this)

    // propagate local updates
    this.document.on("update", (update) => {
      socket.emit("send-update", new Uint8Array(update));
    });

    // listen to remote updates
    socket.on("sync-update", (update) => {
      Y.applyUpdate(document, new Uint8Array(update), null);
    });
  }
}
