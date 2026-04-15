# Web Chat Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight `/chat` web entry so homepage quick prompts can open a chat page, preserve `openid/user_id`, and send the first question to the existing chat API.

**Architecture:** Keep the route thin. The homepage server page normalizes `openid/user_id` and passes the resolved identity into `SearchEntry`, `SearchEntry` links prompts to `/chat`, and a new `ChatWorkspace` client component owns the input, submission state, and first-request auto-send behavior. The existing `/api/chat/messages` API remains unchanged and becomes the single backend integration path for the web chat page.

**Tech Stack:** Next.js App Router, React client components, Testing Library, Vitest

---

## File Map

- Modify: `apps/web/app/page.tsx`
  - Pass the normalized `userId` into the homepage quick prompt component
- Create: `apps/web/app/chat/page.tsx`
  - Normalize `/chat` search params and render the chat workspace
- Create: `apps/web/components/public/chat-workspace.tsx`
  - Render the lightweight chat form, auto-send the initial prompt, and show structured replies
- Modify: `apps/web/components/public/search-entry.tsx`
  - Convert quick prompts from event-only buttons into tracked links to `/chat`
- Create: `apps/web/lib/chat-api.ts`
  - Wrap the `/api/chat/messages` request for the web app
- Modify: `apps/web/tests/public-content.test.tsx`
  - Cover homepage prompt links and click tracking
- Create: `apps/web/tests/chat-page.test.tsx`
  - Cover `/chat` page prop normalization for `openid/user_id/prompt`
- Create: `apps/web/tests/chat-workspace.test.tsx`
  - Cover first-prompt auto-send, manual submit, and rendered reply state
- Create: `apps/web/tests/chat-api.test.ts`
  - Cover request payload shaping for the chat API client

### Task 1: Homepage quick prompts open the chat page

**Files:**
- Modify: `apps/web/app/page.tsx`
- Modify: `apps/web/components/public/search-entry.tsx`
- Modify: `apps/web/tests/public-content.test.tsx`

- [ ] **Step 1: Write the failing homepage prompt test**

Add a test in `apps/web/tests/public-content.test.tsx` that renders `SearchEntry` with `userId="wx-openid-123"` and asserts:

```tsx
expect(screen.getByRole('link', { name: '查学校' })).toHaveAttribute(
  'href',
  '/chat?prompt=%E6%9F%A5%E5%AD%A6%E6%A0%A1&user_id=wx-openid-123',
);
```

- [ ] **Step 2: Run the targeted test to verify failure**

Run:

```powershell
npm test -- public-content.test.tsx
```

Expected: FAIL because quick prompts are still rendered as buttons and `SearchEntry` does not accept `userId`.

- [ ] **Step 3: Implement the minimal homepage prompt link change**

Update `apps/web/app/page.tsx` to pass `userId={userId}` into `SearchEntry`.

Update `apps/web/components/public/search-entry.tsx` to:
- accept `userId?: string`
- build `/chat` links with `prompt` and optional `user_id`
- keep the existing click tracking in the link `onClick`

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```powershell
npm test -- public-content.test.tsx
```

Expected: PASS with the link assertion and tracking test both green.

### Task 2: Add a typed web chat API client

**Files:**
- Create: `apps/web/lib/chat-api.ts`
- Create: `apps/web/tests/chat-api.test.ts`

- [ ] **Step 1: Write the failing API client test**

Create `apps/web/tests/chat-api.test.ts` with a test that stubs `fetch` and asserts `sendChatMessage()` posts:

```ts
{
  channel: 'web',
  user_id: 'wx-openid-123',
  message: '帮我分析江苏985',
  metadata: {
    source: 'web_chat_page',
  },
}
```

- [ ] **Step 2: Run the targeted test to verify failure**

Run:

```powershell
npm test -- chat-api.test.ts
```

Expected: FAIL because `../lib/chat-api` does not exist.

- [ ] **Step 3: Implement the minimal API client**

Create `apps/web/lib/chat-api.ts` with:
- a `sendChatMessage()` helper
- explicit API base URL resolution
- a typed response shape for `summary`, `analysis`, `follow_up_questions`, and `rendered_reply`

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```powershell
npm test -- chat-api.test.ts
```

Expected: PASS with the request payload assertion green.

### Task 3: Add the `/chat` page and client workspace

**Files:**
- Create: `apps/web/app/chat/page.tsx`
- Create: `apps/web/components/public/chat-workspace.tsx`
- Create: `apps/web/tests/chat-page.test.tsx`
- Create: `apps/web/tests/chat-workspace.test.tsx`

- [ ] **Step 1: Write the failing page and workspace tests**

Create `apps/web/tests/chat-page.test.tsx` with a test that mocks `ChatWorkspace` and asserts:
- `/chat?openid=wx-openid-123&prompt=查学校` passes `userId="wx-openid-123"`
- `/chat?user_id=user-1&prompt=查专业` passes `userId="user-1"`

Create `apps/web/tests/chat-workspace.test.tsx` with tests that:
- auto-send `initialPrompt` on first render
- render the returned `rendered_reply`
- allow manual input submission when no initial prompt is provided

- [ ] **Step 2: Run the targeted tests to verify failure**

Run:

```powershell
npm test -- chat-page.test.tsx chat-workspace.test.tsx
```

Expected: FAIL because the `/chat` page and `ChatWorkspace` do not exist.

- [ ] **Step 3: Implement the minimal chat page and workspace**

Create `apps/web/app/chat/page.tsx` to:
- accept `searchParams`
- normalize `user_id` first, then `openid`
- trim `prompt`
- render `ChatWorkspace`

Create `apps/web/components/public/chat-workspace.tsx` to:
- render a heading, textarea, and submit button
- initialize the textarea from `initialPrompt`
- auto-send once when `initialPrompt` exists
- show loading, error, and reply content states
- call `sendChatMessage()` with `channel: 'web'`

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run:

```powershell
npm test -- chat-page.test.tsx chat-workspace.test.tsx
```

Expected: PASS with normalized prop handling and chat submission behavior green.

### Task 4: Run slice verification and commit

**Files:**
- Modify: `apps/web/app/page.tsx`
- Create: `apps/web/app/chat/page.tsx`
- Create: `apps/web/components/public/chat-workspace.tsx`
- Modify: `apps/web/components/public/search-entry.tsx`
- Create: `apps/web/lib/chat-api.ts`
- Modify: `apps/web/tests/public-content.test.tsx`
- Create: `apps/web/tests/chat-page.test.tsx`
- Create: `apps/web/tests/chat-workspace.test.tsx`
- Create: `apps/web/tests/chat-api.test.ts`

- [ ] **Step 1: Run the full targeted web verification**

Run:

```powershell
npm test -- public-content.test.tsx chat-api.test.ts chat-page.test.tsx chat-workspace.test.tsx public-pages.test.tsx
```

Expected: PASS with the new chat slice and existing public page coverage green.

- [ ] **Step 2: Review the diff**

Run:

```powershell
git diff -- apps/web/app/page.tsx apps/web/app/chat/page.tsx apps/web/components/public/search-entry.tsx apps/web/components/public/chat-workspace.tsx apps/web/lib/chat-api.ts apps/web/tests/public-content.test.tsx apps/web/tests/chat-api.test.ts apps/web/tests/chat-page.test.tsx apps/web/tests/chat-workspace.test.tsx
```

Expected: Only the lightweight chat-entry slice is present.

- [ ] **Step 3: Commit the slice**

Run:

```powershell
git add apps/web/app/page.tsx apps/web/app/chat/page.tsx apps/web/components/public/search-entry.tsx apps/web/components/public/chat-workspace.tsx apps/web/lib/chat-api.ts apps/web/tests/public-content.test.tsx apps/web/tests/chat-api.test.ts apps/web/tests/chat-page.test.tsx apps/web/tests/chat-workspace.test.tsx docs/superpowers/plans/2026-04-15-web-chat-entry.md
git commit -m "feat(web): add lightweight chat entry"
```
