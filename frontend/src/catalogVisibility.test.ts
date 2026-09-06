import { describe, expect, it } from 'vitest';
import type { CatalogItem } from './api/types';
import { participantCatalog } from './catalogVisibility';


const item = (catalog_item_id: string, status: CatalogItem['status']): CatalogItem => ({
  catalog_item_id,
  display_name: catalog_item_id,
  description: catalog_item_id,
  category: 'guided_build',
  version: '1.0.0',
  status,
  required_capabilities: [],
  optional_capabilities: [],
  metadata: {},
});


describe('participant catalog visibility', () => {
  it('shows only active catalog items in participant ordering surfaces', () => {
    const items = [
      item('ready', 'active'),
      item('importing', 'draft'),
      item('retired', 'deprecated'),
    ];

    expect(participantCatalog(items).map((entry) => entry.catalog_item_id)).toEqual([
      'ready',
    ]);
  });
});
