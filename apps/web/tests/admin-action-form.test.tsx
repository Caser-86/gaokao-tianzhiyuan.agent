import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';

import AdminActionForm from '../components/admin/admin-action-form';

test('renders a failed server action result inside the submitting form', async () => {
  const action = vi.fn(async () => ({ ok: false, message: '后端保存失败' }));

  render(
    <AdminActionForm action={action}>
      <input name="slug" defaultValue="demo" />
      <button type="submit">保存</button>
    </AdminActionForm>,
  );

  fireEvent.submit(screen.getByRole('button', { name: '保存' }).closest('form') as HTMLFormElement);

  await waitFor(() => {
    expect(action).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('alert')).toHaveTextContent('后端保存失败');
  });
});
