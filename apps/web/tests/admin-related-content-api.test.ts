import { afterEach, expect, test, vi } from 'vitest';

import { listRelatedContent } from '../lib/admin-related-content-api';

afterEach(() => {
  vi.unstubAllGlobals();
});

test('maps admin related content payload', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        schools: [
          {
            slug: 'southeast-university',
            name: '东南大学',
            related_majors: ['clinical-medicine', 'architecture'],
          },
        ],
        majors: [
          {
            slug: 'clinical-medicine',
            name: '临床医学',
            related_schools: ['southeast-university'],
          },
        ],
      }),
    }),
  );

  const payload = await listRelatedContent();

  expect(payload.schools[0].relatedMajors).toEqual([
    'clinical-medicine',
    'architecture',
  ]);
  expect(payload.majors[0].relatedSchools).toEqual(['southeast-university']);
});
