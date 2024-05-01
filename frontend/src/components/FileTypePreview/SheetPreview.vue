<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full text-neutral-100 mx-auto"
  />
  <div>
    <div v-if="loading" v-once id="gridctr" />
  </div>
</template>
<script setup>
import { LoadingIndicator } from "frappe-ui"
import { ref, onBeforeUnmount, onMounted, watch, computed } from "vue"
import { read, utils } from "xlsx"
import Spreadsheet from "x-data-spreadsheet"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: null,
  },
})

const loading = ref(true)
const canWrite = computed(() => {
  return props.previewEntity.owner == "You"
    ? true
    : props.previewEntity.write
    ? true
    : false
})
let grid
async function fetchContent() {
  loading.value = true
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "X-Frappe-Site-Name": window.location.hostname,
    Range: "bytes=0-10000000",
  }
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
    {
      method: "GET",
      headers,
    }
  )
  if (res.ok) {
    const ab = await res.arrayBuffer()
    grid = new Spreadsheet(document.getElementById("gridctr"), {
      /* mode: canWrite.value ? "edit" : "read", */
      /* showToolbar: canWrite.value, */
      mode: "read",
      showToolbar: false,
      showContextmenu: canWrite.value,
      view: {
        height: () => document.getElementById("renderContainer").clientHeight,
        width: () => 1200,
      },
    })
    grid.loadData(stox(read(ab)))
    loading.value = false
  }
}

function stox(wb) {
  var out = []
  wb.SheetNames.forEach(function (name) {
    var o = { name: name, rows: {} }
    var ws = wb.Sheets[name]
    if (!ws || !ws["!ref"]) return
    var range = utils.decode_range(ws["!ref"])
    // sheet_to_json will lost empty row and col at begin as default
    range.s = { r: 0, c: 0 }
    var aoa = utils.sheet_to_json(ws, {
      raw: false,
      header: 1,
      range: range,
    })

    aoa.forEach(function (r, i) {
      var cells = {}
      r.forEach(function (c, j) {
        cells[j] = { text: c || String(c) }

        var cellRef = utils.encode_cell({ r: i, c: j })

        if (ws[cellRef] != null && ws[cellRef].f != null) {
          cells[j].text = "=" + ws[cellRef].f
        }
      })
      o.rows[i] = { cells: cells }
    })
    o.rows.len = aoa.length

    o.merges = []
    ;(ws["!merges"] || []).forEach(function (merge, i) {
      //Needed to support merged cells with empty content
      if (o.rows[merge.s.r] == null) {
        o.rows[merge.s.r] = { cells: {} }
      }
      if (o.rows[merge.s.r].cells[merge.s.c] == null) {
        o.rows[merge.s.r].cells[merge.s.c] = {}
      }

      o.rows[merge.s.r].cells[merge.s.c].merge = [
        merge.e.r - merge.s.r,
        merge.e.c - merge.s.c,
      ]

      o.merges[i] = utils.encode_range(merge)
    })

    out.push(o)
  })

  return out
}

/* function xtos(sdata) {
  var out = utils.book_new();
  sdata.forEach(function (xws) {
    var ws = {};
    var rowobj = xws.rows;
    var minCoord = { r: 0, c: 0 },
      maxCoord = { r: 0, c: 0 };
    for (var ri = 0; ri < rowobj.len; ++ri) {
      var row = rowobj[ri];
      if (!row) continue;

      Object.keys(row.cells).forEach(function (k) {
        var idx = +k;
        if (isNaN(idx)) return;

        var lastRef = utils.encode_cell({ r: ri, c: idx });
        if (ri > maxCoord.r) maxCoord.r = ri;
        if (idx > maxCoord.c) maxCoord.c = idx;

        var cellText = row.cells[k].text,
          type = "s";
        if (!cellText) {
          cellText = "";
          type = "z";
        } else if (!isNaN(Number(cellText))) {
          cellText = Number(cellText);
          type = "n";
        } else if (
          cellText.toLowerCase() === "true" ||
          cellText.toLowerCase() === "false"
        ) {
          cellText = Boolean(cellText);
          type = "b";
        }

        ws[lastRef] = { v: cellText, t: type };

        if (type == "s" && cellText[0] == "=") {
          ws[lastRef].f = cellText.slice(1);
        }

        if (row.cells[k].merge != null) {
          if (ws["!merges"] == null) ws["!merges"] = [];

          ws["!merges"].push({
            s: { r: ri, c: idx },
            e: {
              r: ri + row.cells[k].merge[0],
              c: idx + row.cells[k].merge[1],
            },
          });
        }
      });
    }
    ws["!ref"] = minCoord
      ? utils.encode_range({
          s: minCoord,
          e: maxCoord,
        })
      : "A1";

    utils.book_append_sheet(out, ws, xws.name);
  });
  return out;
} */

watch(
  () => props.previewEntity,
  () => {
    document.getElementById("gridctr").innerHTML = ""
    fetchContent()
  }
)

onMounted(() => {
  fetchContent()
})

onBeforeUnmount(() => {
  loading.value = true
  document.getElementById("gridctr").remove()
})
</script>

<style scoped>
#gridctr {
  display: flex;
}
</style>
