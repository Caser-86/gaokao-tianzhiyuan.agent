import { render, screen } from '@testing-library/react';
import PageSectionRenderer from '../components/public/page-section-renderer';
import SearchEntry from '../components/public/search-entry';

test('renders modular public sections', () => {
  render(
    <PageSectionRenderer
      sections={[
        {
          type: 'highlights',
          title: '学校亮点',
          items: ['工科强', '实习机会多'],
        },
        {
          type: 'pitfalls',
          title: '报考坑点',
          items: ['转专业难', '热门专业分流强'],
        },
      ]}
    />,
  );

  expect(screen.getByRole('heading', { name: '学校亮点' })).toBeInTheDocument();
  expect(screen.getByText('工科强')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '报考坑点' })).toBeInTheDocument();
  expect(screen.getByText('转专业难')).toBeInTheDocument();
});

test('renders search entry prompts for candidates and parents', () => {
  render(
    <SearchEntry
      title="高考志愿助手"
      description="帮你看学校、专业、地域、就业和坑点。"
      quickPrompts={['查学校', '查专业', '看地域对比']}
    />,
  );

  expect(screen.getByRole('heading', { name: '高考志愿助手' })).toBeInTheDocument();
  expect(screen.getByText('帮你看学校、专业、地域、就业和坑点。')).toBeInTheDocument();
  expect(screen.getByText('查学校')).toBeInTheDocument();
  expect(screen.getByText('看地域对比')).toBeInTheDocument();
});
