'use client';

import { useActionState, type ReactNode } from 'react';

export type AdminActionResult = {
  ok: boolean;
  message: string;
};

export type AdminAction = (formData: FormData) => Promise<AdminActionResult | void>;

const initialState: AdminActionResult = {
  ok: true,
  message: '',
};

export default function AdminActionForm({
  action,
  children,
}: {
  action: AdminAction;
  children: ReactNode;
}) {
  const [state, formAction, isPending] = useActionState(
    async (_previousState: AdminActionResult, formData: FormData): Promise<AdminActionResult> => {
      const result = await action(formData);
      return result ?? initialState;
    },
    initialState,
  );

  return (
    <form action={formAction} aria-busy={isPending}>
      {children}
      {isPending ? <p aria-live="polite">提交中…</p> : null}
      {state.message ? (
        <p role={state.ok ? undefined : 'alert'} aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
