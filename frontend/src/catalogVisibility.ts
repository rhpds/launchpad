import type { CatalogItem } from './api/types';


export function participantCatalog(items: CatalogItem[]): CatalogItem[] {
  return items.filter((item) => item.status === 'active');
}
