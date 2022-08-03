import fuzzysort from 'fuzzysort';

export function getFilteredEntities(search, entities) {
  return fuzzysort
    .go(search, entities, {
      limit: 100,
      threshold: -100000,
      key: 'title',
      all: true,
    })
    .map((result) => result.obj);
}
