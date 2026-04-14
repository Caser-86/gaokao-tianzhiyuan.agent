import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

import DashboardShell from '../components/admin/dashboard-shell';

const { listReviewQueueMock, listFeaturedContentMock } = vi.hoisted(() => ({
  listReviewQueueMock: vi.fn(),
  listFeaturedContentMock: vi.fn(),
}));

vi.mock('../lib/admin-review-api', () => ({
  listReviewQueue: listReviewQueueMock,
}));

vi.mock('../lib/admin-featured-content-api', () => ({
  listFeaturedContent: listFeaturedContentMock,
}));

vi.mock('../app/(admin)/admin/actions', () => ({
  approveReviewQueueAction: async () => undefined,
  rejectReviewQueueAction: async () => undefined,
  updateFeaturedSchoolAction: async () => undefined,
  updateFeaturedMajorAction: async () => undefined,
  updateSchoolRotationAction: async () => undefined,
  updateMajorRotationAction: async () => undefined,
}));

import AdminPage from '../app/(admin)/admin/page';

const schoolRotation = {
  enabled: true,
  frequencyDays: 1,
  windowSize: 2,
  orderedSlugs: ['west-china-medical-center', 'wuhan-university'],
};

const majorRotation = {
  enabled: false,
  frequencyDays: 3,
  windowSize: 1,
  orderedSlugs: ['clinical-medicine'],
};

beforeEach(() => {
  listReviewQueueMock.mockReset();
  listFeaturedContentMock.mockReset();
});

test('filters school configuration down to recently scheduled missing-image schools only', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
          isFeatured: true,
          heroImageUrl: '',
        },
        {
          slug: 'wuhan-university',
          name: '武汉大学',
          isFeatured: true,
          heroImageUrl: '',
        },
      ]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
        },
      ]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      showScheduledMissingImageSchoolsOnly
      showScheduledMissingImageSchoolsOnlyHref="/admin?scheduled_missing_school_images=1"
      showMissingImageSchoolsOnlyHref="/admin?missing_school_images=1"
      showAllFeaturedSchoolsHref="/admin"
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByRole('link', { name: '查看全部学校' })).toHaveAttribute('href', '/admin');
  expect(screen.getByRole('link', { name: '仅看待补图片学校（2）' })).toHaveAttribute(
    'href',
    '/admin?missing_school_images=1',
  );
  expect(document.getElementById('featured-school-west-china-medical-center')).not.toBeNull();
  expect(document.getElementById('featured-school-wuhan-university')).toBeNull();
});

test('shows missing-image counts in school configuration filter shortcuts', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
          isFeatured: true,
          heroImageUrl: '',
        },
        {
          slug: 'wuhan-university',
          name: '武汉大学',
          isFeatured: true,
          heroImageUrl: '',
        },
        {
          slug: 'southeast-university',
          name: '东南大学',
          isFeatured: true,
          heroImageUrl: 'https://cdn.example.com/southeast.jpg',
        },
      ]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[
        {
          slug: 'west-china-medical-center',
          name: '华西医学中心',
        },
      ]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[
        {
          slug: 'southeast-university',
          name: '东南大学',
        },
      ]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      showMissingImageSchoolsOnlyHref="/admin?missing_school_images=1"
      showScheduledMissingImageSchoolsOnlyHref="/admin?scheduled_missing_school_images=1"
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(
    screen.getByRole('link', { name: '仅看待补图片学校（2）' }),
  ).toHaveAttribute('href', '/admin?missing_school_images=1');
  expect(
    screen.getByRole('link', { name: '仅看近期缺图学校（1）' }),
  ).toHaveAttribute('href', '/admin?scheduled_missing_school_images=1');
});

test('preserves the selected preview date when linking into the scheduled missing-image filter', async () => {
  listReviewQueueMock.mockResolvedValue([]);
  listFeaturedContentMock.mockResolvedValue({
    schools: [
      {
        slug: 'west-china-medical-center',
        name: '内容候补学校',
        isFeatured: true,
        heroImageUrl: '',
      },
    ],
    majors: [],
    rotation: {
      schools: schoolRotation,
      majors: majorRotation,
    },
    preview: {
      today: {
        schools: [
          {
            slug: 'west-china-medical-center',
            name: '内容候补学校',
          },
        ],
        majors: [],
      },
      next: { schools: [], majors: [] },
      schedule: [],
      selectedDate: null,
      selectedDateError: null,
    },
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        preview_date: '2026-04-15',
      }),
    }),
  );

  const recentFilterLink = screen.getByRole('link', { name: '仅看近期缺图学校（1）' });
  const recentFilterUrl = new URL(recentFilterLink.getAttribute('href') ?? '', 'https://example.com');

  expect(recentFilterUrl.pathname).toBe('/admin');
  expect(recentFilterUrl.searchParams.get('preview_date')).toBe('2026-04-15');
  expect(recentFilterUrl.searchParams.get('scheduled_missing_school_images')).toBe('1');
});
