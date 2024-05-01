import fuzzysort from "fuzzysort"

export default function getFilteredEntities(search, entities) {
  return fuzzysort
    .go(search, entities, {
      limit: 5,
      threshold: -100000,
      key: "title",
      all: true,
    })
    .map((result) => result.obj)
}
