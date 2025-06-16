import { diff, diffCleanupSemantic } from "diff-match-patch-es"
import { Fragment, Node } from "prosemirror-model"
import { DiffType } from "./extensions/diffType"

// function to add marks on a document node by node
export const patchDocumentNode = (schema, oldNode, newNode) => {
  assertNodeTypeEqual(oldNode, newNode)

  const finalLeftChildren = []
  const finalRightChildren = []

  // normlize, compare, and store children
  const oldChildren = normalizeNodeContent(oldNode)
  const newChildren = normalizeNodeContent(newNode)

  const oldChildLen = oldChildren.length
  const newChildLen = newChildren.length

  const minChildLen = Math.min(oldChildLen, newChildLen)

  // ptrs for travel on both sides
  let left = 0 // old
  let right = 0 // new

  // find matching from looping left
  for (; left < minChildLen; left++) {
    const oldChild = oldChildren[left]
    const newChild = newChildren[left]
    // break if diff
    if (!isNodeEqual(oldChild, newChild)) {
      break
    }
    // store if same
    finalLeftChildren.push(...ensureArray(oldChild))
  }

  // same as above but right side
  // can probably skip this extra loop
  for (; right + left + 1 < minChildLen; right++) {
    const oldChild = oldChildren[oldChildLen - right - 1]
    const newChild = newChildren[newChildLen - right - 1]
    if (!isNodeEqual(oldChild, newChild)) {
      break
    }
    finalRightChildren.unshift(...ensureArray(oldChild))
  }

  // different nodes
  const diffOldChildren = oldChildren.slice(left, oldChildLen - right)
  const diffNewChildren = newChildren.slice(left, newChildLen - right)

  if (diffOldChildren.length && diffNewChildren.length) {
    // match nodes between differing children
    const matchedNodes = matchNodes(
      schema,
      diffOldChildren,
      diffNewChildren
    ).sort((a, b) => b.count - a.count) // sort by descending node count

    const bestMatch = matchedNodes[0] // Get the best match (most common)

    if (bestMatch) {
      // destructure idx from highest match
      const { oldStartIndex, newStartIndex, oldEndIndex, newEndIndex } =
        bestMatch

      // get child before match
      const oldBeforeMatchChildren = diffOldChildren.slice(0, oldStartIndex)
      const newBeforeMatchChildren = diffNewChildren.slice(0, newStartIndex)

      // add and patch remaining and add to final left (old)
      finalLeftChildren.push(
        ...patchRemainNodes(
          schema,
          oldBeforeMatchChildren,
          newBeforeMatchChildren
        )
      )
      finalLeftChildren.push(
        ...diffOldChildren.slice(oldStartIndex, oldEndIndex)
      )

      // Get children after the matched nodes from both arrays.
      const oldAfterMatchChildren = diffOldChildren.slice(oldEndIndex)
      const newAfterMatchChildren = diffNewChildren.slice(newEndIndex)

      // Patch remaining nodes after the match and add to finalRightChildren.
      finalRightChildren.unshift(
        ...patchRemainNodes(
          schema,
          oldAfterMatchChildren,
          newAfterMatchChildren
        )
      )
    } else {
      // If no best match is found, simply patch remaining nodes directly.
      finalLeftChildren.push(
        ...patchRemainNodes(schema, diffOldChildren, diffNewChildren)
      )
    }
  } else {
    // If there are no differing children in one of the arrays, patch remaining nodes directly.
    finalLeftChildren.push(
      ...patchRemainNodes(schema, diffOldChildren, diffNewChildren)
    )
  }

  // make new patched node
  return createNewNode(oldNode, [...finalLeftChildren, ...finalRightChildren])
}

const matchNodes = (schema, oldChildren, newChildren) => {
  const matches = []

  for (
    let oldStartIndex = 0;
    oldStartIndex < oldChildren.length;
    oldStartIndex++
  ) {
    const oldStartNode = oldChildren[oldStartIndex]

    // find the index of the matching node in the new children array
    const newStartIndex = findMatchNode(newChildren, oldStartNode)

    // if match then find range of matching nodes
    if (newStartIndex !== -1) {
      let oldEndIndex = oldStartIndex + 1
      let newEndIndex = newStartIndex + 1
      // keep going for a match until none
      for (
        ;
        oldEndIndex < oldChildren.length && newEndIndex < newChildren.length;
        oldEndIndex++, newEndIndex++
      ) {
        const oldEndNode = oldChildren[oldEndIndex]
        if (!isNodeEqual(newChildren[newEndIndex], oldEndNode)) {
          break
        }
      }
      matches.push({
        oldStartIndex,
        newStartIndex,
        oldEndIndex,
        newEndIndex,
        count: newEndIndex - newStartIndex,
      })
    }
  }
  return matches
}

// find matching nodes in children from given idx
const findMatchNode = (children, node, startIndex = 0) => {
  for (let i = startIndex; i < children.length; i++) {
    if (isNodeEqual(children[i], node)) {
      return i
    }
  }
  return -1
}

// usually completely different nodes with
const patchRemainNodes = (schema, oldChildren, newChildren) => {
  const finalLeftChildren = []
  const finalRightChildren = []
  const oldChildLen = oldChildren.length
  const newChildLen = newChildren.length
  let left = 0
  let right = 0
  while (oldChildLen - left - right > 0 && newChildLen - left - right > 0) {
    const leftOldNode = oldChildren[left]
    const leftNewNode = newChildren[left]
    const rightOldNode = oldChildren[oldChildLen - right - 1]
    const rightNewNode = newChildren[newChildLen - right - 1]
    let updateLeft =
      !isTextNode(leftOldNode) && matchNodeType(leftOldNode, leftNewNode)
    let updateRight =
      !isTextNode(rightOldNode) && matchNodeType(rightOldNode, rightNewNode)
    if (Array.isArray(leftOldNode) && Array.isArray(leftNewNode)) {
      finalLeftChildren.push(
        ...patchTextNodes(schema, leftOldNode, leftNewNode)
      )
      left += 1
      continue
    }

    if (updateLeft && updateRight) {
      const equalityLeft = computeChildEqualityFactor(leftOldNode, leftNewNode)
      const equalityRight = computeChildEqualityFactor(
        rightOldNode,
        rightNewNode
      )
      if (equalityLeft < equalityRight) {
        updateLeft = false
      } else {
        updateRight = false
      }
    }
    if (updateLeft) {
      finalLeftChildren.push(
        patchDocumentNode(schema, leftOldNode, leftNewNode)
      )
      left += 1
    } else if (updateRight) {
      finalRightChildren.unshift(
        patchDocumentNode(schema, rightOldNode, rightNewNode)
      )
      right += 1
    } else {
      // todo
      finalLeftChildren.push(
        createDiffNode(schema, leftOldNode, DiffType.Deleted)
      )
      finalLeftChildren.push(
        createDiffNode(schema, leftNewNode, DiffType.Inserted)
      )
      left += 1
      // delete and insert
    }
  }

  const deleteNodeLen = oldChildLen - left - right
  const insertNodeLen = newChildLen - left - right
  if (deleteNodeLen) {
    finalLeftChildren.push(
      ...oldChildren
        .slice(left, left + deleteNodeLen)
        .flat()
        .map((node) => createDiffNode(schema, node, DiffType.Deleted))
    )
  }

  if (insertNodeLen) {
    finalRightChildren.unshift(
      ...newChildren
        .slice(left, left + insertNodeLen)
        .flat()
        .map((node) => createDiffNode(schema, node, DiffType.Inserted))
    )
  }

  return [...finalLeftChildren, ...finalRightChildren]
}

export const patchTextNodes = (schema, oldNode, newNode) => {
  const oldText = oldNode.map((n) => getNodeText(n)).join("")
  const newText = newNode.map((n) => getNodeText(n)).join("")

  //const diff = dmp.diff_main(oldText, newText)
  //const diff = diffLineMode(oldText, newText)
  //const diff = smartDiff(oldText, newText)
  const dmpDiff = diff(oldText, newText)
  diffCleanupSemantic(dmpDiff)

  //const diff = JsDiff.convertChangesToDMP(smartDiff(oldText, newText))
  let oldLen = 0
  let newLen = 0

  // given a diff generate new nodes with the diff mark and attr from dmp
  const res = dmpDiff
    .map((d) => {
      const [type, content] = [d[0], d[1]]
      const node = createTextNode(
        schema,
        content,
        type !== DiffType.Unchanged ? createDiffMark(schema, type) : []
      )
      const oldFrom = oldLen
      const oldTo = oldFrom + (type === DiffType.Inserted ? 0 : content.length)
      const newFrom = newLen
      const newTo = newFrom + (type === DiffType.Deleted ? 0 : content.length)
      oldLen = oldTo
      newLen = newTo
      return { node, type, oldFrom, oldTo, newFrom, newTo }
    })
    .map(({ node, type, oldFrom, oldTo, newFrom, newTo }) => {
      if (type === DiffType.Deleted) {
        const textItems = findTextNodes(oldNode, oldFrom, oldTo).filter(
          (n) => Object.keys(n.node.attrs ?? {}).length || n.node.marks?.length
        )
        return applyTextNodeAttrsMarks(schema, node, oldFrom, textItems)
      } else {
        const textItems = findTextNodes(newNode, newFrom, newTo).filter(
          (n) => Object.keys(n.node.attrs ?? {}).length || n.node.marks?.length
        )
        return applyTextNodeAttrsMarks(schema, node, newFrom, textItems)
      }
    })
  return res.flat(Infinity)
}

/* function smartDiff(oldContent, newContent) {
  const wordDiffs = JsDiff.diffWords(oldContent, newContent)
  const totalChanges = wordDiffs.reduce((acc, part) => {
    if (part.added) return acc + part.value.split(/\s+/).length
    if (part.removed) return acc + part.value.split(/\s+/).length
    return acc
  }, 0)
  console.log(totalChanges)
  // picked this randomly
  // todo: update
  const threshold = 8

  if (totalChanges <= threshold) {
    return JsDiff.diffChars(oldContent, newContent)
  } else {
    return JsDiff.diffSentences(
      oldContent.replace(/[.!?]/g, "."),
      newContent.replace(/[.!?]/g, ".")
    )
  }
}

 function diffLineMode(text1, text2) {
  var dmp = new diff_match_patch()
  var a = dmp.diff_linesToChars_(text1, text2)
  var lineText1 = a.chars1
  var lineText2 = a.chars2
  var lineArray = a.lineArray
  var diffs = dmp.diff_main(lineText1, lineText2, false)
  dmp.diff_charsToLines_(diffs, lineArray)
  dmp.diff_cleanupSemantic(diffs)
  return diffs
} 
  
function smartDiff(text1, text2) {
  if (!text1 || !text2) return [] // Handle empty inputs

  const dmp = new diff_match_patch()

  // Split texts into sentences
  const sentences1 = text1
    .split(/[.!?]+/)
    .map((s) => s.trim())
    .filter(Boolean)
  const sentences2 = text2
    .split(/[.!?]+/)
    .map((s) => s.trim())
    .filter(Boolean)

  // Perform sentence-level diff
  let sentenceDiff = dmp.diff_main(sentences1.join("\n"), sentences2.join("\n"))
  dmp.diff_cleanupSemantic(sentenceDiff)

  // Check sentence-level diff similarity
  const sentenceSimilarity =
    1 -
    dmp.diff_levenshtein(sentenceDiff) /
      Math.max(sentences1.length, sentences2.length)

  if (sentenceSimilarity > 0.8) {
    return sentenceDiff
  }

  // Split sentences into words
  const words1 = text1.split(/\s+/).filter(Boolean)
  const words2 = text2.split(/\s+/).filter(Boolean)

  // Perform word-level diff
  let wordDiff = dmp.diff_main(words1.join(" "), words2.join(" "))
  dmp.diff_cleanupSemantic(wordDiff)

  // Check word-level diff similarity
  const wordSimilarity =
    1 - dmp.diff_levenshtein(wordDiff) / Math.max(words1.length, words2.length)

  if (wordSimilarity > 0.6) {
    return wordDiff
  }

  // Fallback to character-level diff
  return dmp.diff_main(text1, text2)
}
*/

const findTextNodes = (textNodes, from, to) => {
  const result = []
  let start = 0
  for (let i = 0; i < textNodes.length && start < to; i++) {
    const node = textNodes[i]
    const text = getNodeText(node)
    const end = start + text.length
    const intersect =
      (start >= from && start < to) ||
      (end > from && end <= to) ||
      (start <= from && end >= to)
    if (intersect) {
      result.push({ node, from: start, to: end })
    }
    start += text.length
  }
  return result
}

const applyTextNodeAttrsMarks = (schema, node, base, textItems) => {
  if (!textItems.length) {
    return node
  }

  const baseMarks = node.marks ?? []
  const firstItem = textItems[0]
  const nodeText = getNodeText(node)
  const nodeEnd = base + nodeText.length
  const result = []
  if (firstItem.from - base > 0) {
    result.push(
      createTextNode(
        schema,
        nodeText.slice(0, firstItem.from - base),
        baseMarks
      )
    )
  }
  for (let i = 0; i < textItems.length; i++) {
    const { from, node: textNode, to } = textItems[i]
    result.push(
      createTextNode(
        schema,
        nodeText.slice(Math.max(from, base) - base, to - base),
        [...baseMarks, ...(textNode.marks ?? [])]
      )
    )
    const nextFrom = i + 1 < textItems.length ? textItems[i + 1].from : nodeEnd
    if (nextFrom > to) {
      result.push(
        createTextNode(
          schema,
          nodeText.slice(to - base, nextFrom - base),
          baseMarks
        )
      )
    }
  }
  return result
}

export const computeChildEqualityFactor = (node1, node2) => {
  return 0
}

export const assertNodeTypeEqual = (node1, node2) => {
  if (getNodeProperty(node1, "type") !== getNodeProperty(node2, "type")) {
    throw new Error(`node type not equal: ${node1.type} !== ${node2.type}`)
  }
}

export const ensureArray = (value) => {
  return Array.isArray(value) ? value : [value]
}

export const isNodeEqual = (node1, node2) => {
  const isNode1Array = Array.isArray(node1)
  const isNode2Array = Array.isArray(node2)
  if (isNode1Array !== isNode2Array) {
    return false
  }
  if (isNode1Array) {
    return (
      node1.length === node2.length &&
      node1.every((node, index) => isNodeEqual(node, node2[index]))
    )
  }

  const type1 = getNodeProperty(node1, "type")
  const type2 = getNodeProperty(node2, "type")
  if (type1 !== type2) {
    return false
  }
  if (isTextNode(node1)) {
    const text1 = getNodeProperty(node1, "text")
    const text2 = getNodeProperty(node2, "text")
    if (text1 !== text2) {
      return false
    }
  }
  const attrs1 = getNodeAttributes(node1)
  const attrs2 = getNodeAttributes(node2)
  const attrs = [...new Set([...Object.keys(attrs1), ...Object.keys(attrs2)])]
  for (const attr of attrs) {
    if (attrs1[attr] !== attrs2[attr]) {
      return false
    }
  }
  const marks1 = getNodeMarks(node1)
  const marks2 = getNodeMarks(node2)
  if (marks1.length !== marks2.length) {
    return false
  }
  for (let i = 0; i < marks1.length; i++) {
    if (!isNodeEqual(marks1[i], marks2[i])) {
      return false
    }
  }
  const children1 = getNodeChildren(node1)
  const children2 = getNodeChildren(node2)
  if (children1.length !== children2.length) {
    return false
  }
  for (let i = 0; i < children1.length; i++) {
    if (!isNodeEqual(children1[i], children2[i])) {
      return false
    }
  }
  return true
}

export const normalizeNodeContent = (node) => {
  const content = getNodeChildren(node) ?? []
  const res = []
  for (let i = 0; i < content.length; i++) {
    const child = content[i]

    if (isTextNode(child)) {
      const textNodes = []
      // turn this into a while, this is not readable
      for (
        let textNode = content[i];
        i < content.length && isTextNode(textNode);
        textNode = content[++i]
      ) {
        textNodes.push(textNode)
      }
      i--
      res.push(textNodes)
    } else {
      res.push(child)
    }
  }
  return res
}

// generic node utils
export const getNodeProperty = (node, property) => {
  if (property === "type") {
    return node.type?.name
  }
  return node[property]
}
export const getNodeAttribute = (node, attribute) =>
  node.attrs ? node.attrs[attribute] : undefined
export const getNodeAttributes = (node) => (node.attrs ? node.attrs : undefined)
export const getNodeMarks = (node) => node.marks ?? []
export const getNodeChildren = (node) => node.content?.content ?? []
export const getNodeText = (node) => node.text
export const isTextNode = (node) => node.type?.name === "text"

export const matchNodeType = (node1, node2) =>
  node1.type?.name === node2.type?.name ||
  (Array.isArray(node1) && Array.isArray(node2))

export const createNewNode = (oldNode, children) => {
  if (!oldNode.type) {
    throw new Error("oldNode.type is undefined")
  }
  return new Node(
    oldNode.type,
    oldNode.attrs,
    Fragment.fromArray(children),
    oldNode.marks
  )
}

// node level diff WIP
export const createDiffNode = (schema, node, type) => {
  return mapDocumentNode(node, (currentNode) => {
    if (isTextNode(currentNode)) {
      const textContent = getNodeText(currentNode)
      const marks = [...(currentNode.marks || []), createDiffMark(schema, type)]
      return createTextNode(schema, textContent, marks)
    }
    return currentNode
  })
}

function mapDocumentNode(node, mapper) {
  const mappedContent = node.content.content
    .map((childNode) => mapDocumentNode(childNode, mapper))
    .filter(Boolean) // null/undefined

  const copy = node.copy(Fragment.from(mappedContent))

  return mapper(copy) || copy
}

export const createDiffMark = (schema, type) => {
  const validTypes = [DiffType.Inserted, DiffType.Deleted]
  if (!validTypes.includes(type)) {
    throw new Error("type is not valid")
  }
  return schema.mark("diffMark", { type })
}

export const createTextNode = (schema, content, marks = []) => {
  return schema.text(content, marks)
}

export const generateDiffDocument = (schema, oldDoc, newDoc) => {
  const oldNode = Node.fromJSON(schema, oldDoc)
  const newNode = Node.fromJSON(schema, newDoc)
  return patchDocumentNode(schema, oldNode, newNode)
}
