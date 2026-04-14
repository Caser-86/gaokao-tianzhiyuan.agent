import { afterEach, expect, test, vi } from 'vitest';

import { listContentSections } from '../lib/admin-content-sections-api';

afterEach(() => {
  vi.unstubAllGlobals();
});

test('maps admin content sections payload', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        schools: [
          {
            slug: 'southeast-university',
            name: '东南大学',
            sections: [
              {
                type: 'highlights',
                title: '学校亮点',
                items: ['资源密集'],
              },
            ],
          },
        ],
        majors: [],
      }),
    }),
  );

  const payload = await listContentSections();

  expect(payload.schools[0].sections[0].title).toBe('学校亮点');
});
