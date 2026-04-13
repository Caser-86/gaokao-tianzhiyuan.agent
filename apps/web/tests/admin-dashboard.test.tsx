import { render, screen } from '@testing-library/react';
import DashboardShell from '../components/admin/dashboard-shell';

test('renders admin dashboard heading', () => {
  render(<DashboardShell title="内容运营后台" />);
  expect(screen.getByRole('heading', { name: '内容运营后台' })).toBeInTheDocument();
  expect(screen.getByText('待审核内容')).toBeInTheDocument();
});
