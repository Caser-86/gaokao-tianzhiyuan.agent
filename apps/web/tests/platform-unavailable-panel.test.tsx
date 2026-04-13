import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import PlatformUnavailablePanel from '../components/public/platform-unavailable-panel';

test('renders platform unavailable actions', () => {
  render(<PlatformUnavailablePanel />);

  expect(
    screen.getByRole('heading', { name: '\u5e73\u53f0\u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528' }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('link', { name: '\u5148\u53bb\u67e5\u5b66\u6821' }),
  ).toHaveAttribute('href', '#school-catalog');
  expect(
    screen.getByRole('link', { name: '\u7a0d\u540e\u518d\u8bd5' }),
  ).toHaveAttribute('href', '/');
});
