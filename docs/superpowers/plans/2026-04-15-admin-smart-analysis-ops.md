# Admin Smart Analysis Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SQLite-backed admin controls for the global smart-analysis mode and per-user `smart_analysis` entitlement so operators can manage access without redeploying or hand-editing request metadata.

**Architecture:** Introduce dedicated SQLModel tables and an `access_control` service for runtime setting and per-user entitlement reads/writes. Extend the admin API and admin page to manage those records, then update chat policy resolution to read DB-backed mode and entitlements first while keeping request metadata as a compatibility path.

**Tech Stack:** FastAPI, SQLModel, SQLite, Pydantic/SQLModel request models, pytest, Next.js server actions, Vitest, Testing Library

---

## File Map

- Create: `apps/api/app/models/access_control.py`
  - SQLModel tables for runtime settings and user entitlements
- Modify: `apps/api/app/models/__init__.py`
  - Export/import new models so startup auto-creates them
- Create: `apps/api/app/services/access_control.py`
  - Centralize DB-backed smart-analysis reads/writes and chat-time evaluation helpers
- Create: `apps/api/tests/test_access_control_service.py`
  - TDD coverage for defaults, updates, grants, revokes, and compatibility logic
- Modify: `apps/api/app/routers/admin.py`
  - Add admin endpoints for smart-analysis settings and per-user entitlement management
- Modify: `apps/api/tests/test_admin_api.py`
  - Add admin API coverage for new settings and entitlement endpoints
- Modify: `apps/api/app/services/chat.py`
  - Resolve smart-analysis policy through the new access-control service using `user_id`
- Modify: `apps/api/tests/test_chat_services.py`
  - Add DB-backed smart-analysis gating coverage
- Create: `apps/web/lib/admin-smart-analysis-api.ts`
  - Admin fetch client for smart-analysis settings and user entitlement operations
- Modify: `apps/web/app/(admin)/admin/actions.ts`
  - Add server actions for saving global mode and granting/revoking user access
- Modify: `apps/web/app/(admin)/admin/page.tsx`
  - Load smart-analysis ops data and pass it into the admin shell
- Create: `apps/web/components/admin/smart-analysis-ops-panel.tsx`
  - Focused admin UI block for global mode and per-user entitlement controls
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
  - Render the new smart-analysis panel without bloating existing sections
- Modify: `apps/web/tests/admin-page.test.tsx`
  - Add admin-page loading assertions for smart-analysis data
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
  - Add dashboard rendering assertions for the new controls
- Modify: `apps/api/README.md`
  - Document runtime bootstrap and admin-managed smart-analysis operations

### Task 1: Add DB-backed access-control models and service helpers

**Files:**
- Create: `apps/api/app/models/access_control.py`
- Modify: `apps/api/app/models/__init__.py`
- Create: `apps/api/app/services/access_control.py`
- Create: `apps/api/tests/test_access_control_service.py`

- [ ] **Step 1: Write the failing service tests**

Create `apps/api/tests/test_access_control_service.py` with:

```python
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.services.access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    get_user_entitlements,
    set_smart_analysis_mode,
    set_user_entitlement,
)


def build_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_get_effective_smart_analysis_mode_defaults_to_bootstrap_value() -> None:
    with build_session() as session:
        assert (
            get_effective_smart_analysis_mode(session, default_mode="gated") == "gated"
        )


def test_set_smart_analysis_mode_persists_and_overwrites_existing_value() -> None:
    with build_session() as session:
        assert set_smart_analysis_mode(session, "off") == "off"
        assert set_smart_analysis_mode(session, "on") == "on"
        assert get_effective_smart_analysis_mode(session, default_mode="gated") == "on"


def test_set_user_entitlement_grants_and_revokes_smart_analysis() -> None:
    with build_session() as session:
        set_user_entitlement(
            session,
            user_id="wx-openid-1",
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=True,
        )
        assert get_user_entitlements(session, "wx-openid-1") == ["smart_analysis"]

        set_user_entitlement(
            session,
            user_id="wx-openid-1",
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=False,
        )
        assert get_user_entitlements(session, "wx-openid-1") == []
```

- [ ] **Step 2: Run the tests to verify failure**

Run:

```powershell
python -m pytest tests/test_access_control_service.py -v
```

Expected: FAIL because the access-control models and helpers do not exist yet.

- [ ] **Step 3: Add the new SQLModel tables**

Create `apps/api/app/models/access_control.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str = Field(nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class UserEntitlement(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "entitlement", name="uq_user_entitlements_user_id_entitlement"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(nullable=False, index=True)
    entitlement: str = Field(nullable=False, index=True)
    is_enabled: bool = Field(default=True, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
```

Modify `apps/api/app/models/__init__.py`:

```python
from .access_control import RuntimeSetting, UserEntitlement
from .content import School, SchoolContentVersion
from .ingestion import ReviewQueue

__all__ = [
    "RuntimeSetting",
    "UserEntitlement",
    "School",
    "SchoolContentVersion",
    "ReviewQueue",
]
```

- [ ] **Step 4: Implement the access-control service**

Create `apps/api/app/services/access_control.py`:

```python
from __future__ import annotations

from sqlmodel import Session, select

from ..models.access_control import RuntimeSetting, UserEntitlement

SMART_ANALYSIS_MODE_KEY = "smart_analysis_mode"
SMART_ANALYSIS_ENTITLEMENT = "smart_analysis"
ALLOWED_SMART_ANALYSIS_MODES = {"off", "gated", "on"}


def get_effective_smart_analysis_mode(session: Session, *, default_mode: str) -> str:
    setting = session.get(RuntimeSetting, SMART_ANALYSIS_MODE_KEY)
    if setting is None:
        return default_mode
    return setting.value


def set_smart_analysis_mode(session: Session, mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in ALLOWED_SMART_ANALYSIS_MODES:
        raise ValueError("smart_analysis_mode must be one of: off, gated, on")

    setting = session.get(RuntimeSetting, SMART_ANALYSIS_MODE_KEY)
    if setting is None:
        setting = RuntimeSetting(key=SMART_ANALYSIS_MODE_KEY, value=normalized)
    else:
        setting.value = normalized

    session.add(setting)
    session.commit()
    session.refresh(setting)
    return setting.value


def set_user_entitlement(
    session: Session,
    *,
    user_id: str,
    entitlement: str,
    is_enabled: bool,
) -> UserEntitlement:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id must not be empty")

    statement = select(UserEntitlement).where(
        UserEntitlement.user_id == normalized_user_id,
        UserEntitlement.entitlement == entitlement,
    )
    record = session.exec(statement).one_or_none()
    if record is None:
        record = UserEntitlement(
            user_id=normalized_user_id,
            entitlement=entitlement,
            is_enabled=is_enabled,
        )
    else:
        record.is_enabled = is_enabled

    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_user_entitlements(session: Session, user_id: str) -> list[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []

    statement = select(UserEntitlement).where(
        UserEntitlement.user_id == normalized_user_id,
        UserEntitlement.is_enabled.is_(True),
    )
    return sorted(item.entitlement for item in session.exec(statement).all())
```

- [ ] **Step 5: Run the focused tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_access_control_service.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add apps/api/app/models/access_control.py apps/api/app/models/__init__.py apps/api/app/services/access_control.py apps/api/tests/test_access_control_service.py
git commit -m "feat(api): add smart analysis access control persistence"
```

### Task 2: Add admin API endpoints for runtime mode and per-user entitlement management

**Files:**
- Modify: `apps/api/app/routers/admin.py`
- Modify: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing admin API tests**

Update `apps/api/tests/test_admin_api.py` to add:

```python
def test_smart_analysis_settings_endpoint_returns_bootstrap_default(admin_client) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/smart-analysis/settings",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {"mode": settings.smart_analysis_mode}


def test_update_smart_analysis_settings_persists_mode(admin_client) -> None:
    client, _engine = admin_client

    response = client.put(
        "/api/admin/smart-analysis/settings",
        headers={"x-admin-token": settings.admin_token},
        json={"mode": "gated"},
    )

    assert response.status_code == 200
    assert response.json() == {"mode": "gated"}


def test_smart_analysis_user_entitlement_can_be_granted_and_revoked(admin_client) -> None:
    client, _engine = admin_client

    grant_response = client.put(
        "/api/admin/smart-analysis/users/wx-openid-123",
        headers={"x-admin-token": settings.admin_token},
        json={"smart_analysis_enabled": True},
    )
    assert grant_response.status_code == 200
    assert grant_response.json() == {
        "user_id": "wx-openid-123",
        "entitlements": [{"name": "smart_analysis", "enabled": True}],
    }

    revoke_response = client.put(
        "/api/admin/smart-analysis/users/wx-openid-123",
        headers={"x-admin-token": settings.admin_token},
        json={"smart_analysis_enabled": False},
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json() == {
        "user_id": "wx-openid-123",
        "entitlements": [],
    }
```

- [ ] **Step 2: Run the admin API tests to verify failure**

Run:

```powershell
python -m pytest tests/test_admin_api.py -v
```

Expected: FAIL because the admin smart-analysis endpoints do not exist yet.

- [ ] **Step 3: Add request/response models and routes**

Modify `apps/api/app/routers/admin.py` to add:

```python
class SmartAnalysisSettingsResponse(SQLModel):
    mode: str


class SmartAnalysisSettingsRequest(SQLModel):
    mode: str


class UserEntitlementStatusResponse(SQLModel):
    name: str
    enabled: bool


class SmartAnalysisUserEntitlementsResponse(SQLModel):
    user_id: str
    entitlements: list[UserEntitlementStatusResponse]


class SmartAnalysisUserEntitlementsRequest(SQLModel):
    smart_analysis_enabled: bool
```

and add handlers:

```python
@router.get("/smart-analysis/settings", response_model=SmartAnalysisSettingsResponse)
def get_smart_analysis_settings(
    _admin: str = Depends(require_admin_token),
    session: Session = Depends(get_session),
) -> SmartAnalysisSettingsResponse:
    return SmartAnalysisSettingsResponse(
        mode=get_effective_smart_analysis_mode(
            session,
            default_mode=settings.smart_analysis_mode,
        )
    )


@router.put("/smart-analysis/settings", response_model=SmartAnalysisSettingsResponse)
def update_smart_analysis_settings(
    payload: SmartAnalysisSettingsRequest,
    _admin: str = Depends(require_admin_token),
    session: Session = Depends(get_session),
) -> SmartAnalysisSettingsResponse:
    try:
        mode = set_smart_analysis_mode(session, payload.mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SmartAnalysisSettingsResponse(mode=mode)
```

and:

```python
@router.get(
    "/smart-analysis/users/{user_id}",
    response_model=SmartAnalysisUserEntitlementsResponse,
)
def get_smart_analysis_user_entitlements(
    user_id: str,
    _admin: str = Depends(require_admin_token),
    session: Session = Depends(get_session),
) -> SmartAnalysisUserEntitlementsResponse:
    entitlements = get_user_entitlements(session, user_id)
    return SmartAnalysisUserEntitlementsResponse(
        user_id=user_id,
        entitlements=[
            UserEntitlementStatusResponse(name=name, enabled=True)
            for name in entitlements
        ],
    )


@router.put(
    "/smart-analysis/users/{user_id}",
    response_model=SmartAnalysisUserEntitlementsResponse,
)
def update_smart_analysis_user_entitlements(
    user_id: str,
    payload: SmartAnalysisUserEntitlementsRequest,
    _admin: str = Depends(require_admin_token),
    session: Session = Depends(get_session),
) -> SmartAnalysisUserEntitlementsResponse:
    try:
        set_user_entitlement(
            session,
            user_id=user_id,
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=payload.smart_analysis_enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    entitlements = get_user_entitlements(session, user_id)
    return SmartAnalysisUserEntitlementsResponse(
        user_id=user_id,
        entitlements=[
            UserEntitlementStatusResponse(name=name, enabled=True)
            for name in entitlements
        ],
    )
```

- [ ] **Step 4: Run the admin API tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_admin_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add apps/api/app/routers/admin.py apps/api/tests/test_admin_api.py
git commit -m "feat(api): add admin smart analysis ops endpoints"
```

### Task 3: Wire chat policy resolution to DB-backed runtime mode and per-user entitlement

**Files:**
- Modify: `apps/api/app/services/chat.py`
- Modify: `apps/api/tests/test_chat_services.py`

- [ ] **Step 1: Write the failing chat service tests**

Update `apps/api/tests/test_chat_services.py` to add:

```python
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.services.access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    set_smart_analysis_mode,
    set_user_entitlement,
)


def build_chat_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_conversation_service_uses_db_entitlement_when_mode_is_gated(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("张雪峰测试提示词", encoding="utf-8")

    with build_chat_session() as session:
        set_smart_analysis_mode(session, "gated")
        set_user_entitlement(
            session,
            user_id="wx-openid-db-1",
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=True,
        )
        service = ConversationService(
            registry=SkillRegistry(
                [
                    ZhangXueFengSkill(
                        provider=FakeProvider(
                            '{"intent":"major_recommendation","summary":"建议避开金融","analysis":"数据库权益已生效","suggestions":[],"follow_up_questions":[],"actions":[],"risk_flags":[],"rendered_reply":"ok"}'
                        ),
                        skill_prompt_path=str(skill_file),
                    )
                ]
            ),
            session_factory=lambda: session,
        )

        result = service.handle_message(
            channel="wechat",
            user_id="wx-openid-db-1",
            message="河南560分想学金融，靠谱吗？",
        )

    assert result["output"]["content"]["analysis"] == "数据库权益已生效"
    assert result["debug"] == {"used_fallback": False, "notes": []}
```

- [ ] **Step 2: Run the focused chat tests to verify failure**

Run:

```powershell
python -m pytest tests/test_chat_services.py -v
```

Expected: FAIL because `ConversationService` does not use DB-backed smart-analysis state yet.

- [ ] **Step 3: Add session-aware chat resolution**

Modify `apps/api/app/services/chat.py` so the constructor can accept a session factory:

```python
from collections.abc import Callable

from sqlmodel import Session

from ..db import get_engine
from .access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    get_user_entitlements,
)


class ConversationService:
    def __init__(
        self,
        registry: SkillRegistry | None = None,
        threshold: float = ROUTING_THRESHOLD,
        session_factory: Callable[[], Session] | None = None,
    ) -> None:
        self.registry = registry or build_default_registry()
        self.threshold = threshold
        self.session_factory = session_factory or (lambda: Session(get_engine()))
```

Then replace the direct `resolve_smart_analysis_decision(...)` usage with:

```python
        with self.session_factory() as session:
            persisted_mode = get_effective_smart_analysis_mode(
                session,
                default_mode=settings.smart_analysis_mode,
            )
            persisted_entitlements = get_user_entitlements(session, user_id)

        metadata_entitlements = (
            metadata.get("entitlements", [])
            if isinstance((metadata or {}).get("entitlements"), list)
            else []
        )
        merged_metadata = {
            **(metadata or {}),
            "entitlements": sorted({*persisted_entitlements, *metadata_entitlements}),
        }
        smart_analysis_allowed, smart_analysis_reason = resolve_smart_analysis_decision(
            merged_metadata,
            default_mode=persisted_mode,
        )
```

- [ ] **Step 4: Run the focused chat tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_chat_services.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add apps/api/app/services/chat.py apps/api/tests/test_chat_services.py
git commit -m "feat(api): resolve smart analysis access from sqlite"
```

### Task 4: Add admin web client, server actions, and UI controls

**Files:**
- Create: `apps/web/lib/admin-smart-analysis-api.ts`
- Modify: `apps/web/app/(admin)/admin/actions.ts`
- Modify: `apps/web/app/(admin)/admin/page.tsx`
- Create: `apps/web/components/admin/smart-analysis-ops-panel.tsx`
- Modify: `apps/web/components/admin/dashboard-shell.tsx`
- Modify: `apps/web/tests/admin-page.test.tsx`
- Modify: `apps/web/tests/admin-dashboard.test.tsx`
- Modify: `apps/api/README.md`

- [ ] **Step 1: Write the failing frontend tests**

Update `apps/web/tests/admin-page.test.tsx` mocks to include the new API client:

```typescript
const {
  listSmartAnalysisSettingsMock,
  getSmartAnalysisUserMock,
} = vi.hoisted(() => ({
  listSmartAnalysisSettingsMock: vi.fn(),
  getSmartAnalysisUserMock: vi.fn(),
}));

vi.mock('../lib/admin-smart-analysis-api', () => ({
  getSmartAnalysisSettings: listSmartAnalysisSettingsMock,
  getSmartAnalysisUser: getSmartAnalysisUserMock,
}));
```

Add a page test:

```typescript
test('renders smart analysis admin controls from admin api clients', async () => {
  listSmartAnalysisSettingsMock.mockResolvedValue({ mode: 'gated' });
  getSmartAnalysisUserMock.mockResolvedValue({
    userId: 'wx-openid-123',
    entitlements: [{ name: 'smart_analysis', enabled: true }],
  });

  render(
    await AdminPage({
      searchParams: Promise.resolve({
        smart_analysis_user_id: 'wx-openid-123',
      }),
    }),
  );

  expect(screen.getByRole('heading', { name: '智能分析权限运营' })).toBeInTheDocument();
  expect(screen.getByDisplayValue('gated')).toBeInTheDocument();
  expect(screen.getByDisplayValue('wx-openid-123')).toBeInTheDocument();
  expect(screen.getByText('当前已开通智能分析')).toBeInTheDocument();
});
```

Add a dashboard-shell test:

```typescript
test('renders smart analysis ops panel with mode and per-user controls', () => {
  render(
    <DashboardShell
      title="内容运营后台"
      queueItems={[]}
      featuredSchools={[]}
      featuredMajors={[]}
      schoolRotation={schoolRotation}
      majorRotation={majorRotation}
      featuredSchoolPreview={[]}
      featuredMajorPreview={[]}
      nextFeaturedSchoolPreview={[]}
      nextFeaturedMajorPreview={[]}
      featuredSchedule={[]}
      selectedPreviewDateValue=""
      selectedDatePreview={null}
      smartAnalysisMode="gated"
      smartAnalysisUserId="wx-openid-123"
      smartAnalysisUserEnabled={true}
      loadSmartAnalysisUserHref="/admin?smart_analysis_user_id=wx-openid-123"
      updateSmartAnalysisModeAction={async () => undefined}
      updateSmartAnalysisUserAction={async () => undefined}
      approveAction={async () => undefined}
      rejectAction={async () => undefined}
      updateFeaturedSchoolAction={async () => undefined}
      updateFeaturedMajorAction={async () => undefined}
      updateSchoolRotationAction={async () => undefined}
      updateMajorRotationAction={async () => undefined}
    />,
  );

  expect(screen.getByRole('heading', { name: '智能分析权限运营' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '保存智能分析模式' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '开通智能分析' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '关闭智能分析' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the frontend tests to verify failure**

Run:

```powershell
pnpm --filter web test admin-page.test.tsx admin-dashboard.test.tsx
```

Expected: FAIL because the smart-analysis admin client, props, and UI do not exist yet.

- [ ] **Step 3: Add the admin web client**

Create `apps/web/lib/admin-smart-analysis-api.ts`:

```typescript
import 'server-only';

const getApiUrl = () => process.env.GAOKAO_AGENT_API_URL ?? 'http://127.0.0.1:8000';
const getAdminToken = () => process.env.GAOKAO_AGENT_ADMIN_TOKEN ?? 'dev-admin-token';

const buildHeaders = (contentType?: string) => {
  const headers: Record<string, string> = { 'x-admin-token': getAdminToken() };
  if (contentType) {
    headers['Content-Type'] = contentType;
  }
  return headers;
};

const parseResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
};

export async function getSmartAnalysisSettings(): Promise<{ mode: string }> {
  const response = await fetch(`${getApiUrl()}/api/admin/smart-analysis/settings`, {
    headers: buildHeaders(),
    cache: 'no-store',
  });
  return parseResponse<{ mode: string }>(response);
}

export async function getSmartAnalysisUser(userId: string): Promise<{
  userId: string;
  entitlements: Array<{ name: string; enabled: boolean }>;
}> {
  const response = await fetch(
    `${getApiUrl()}/api/admin/smart-analysis/users/${encodeURIComponent(userId)}`,
    {
      headers: buildHeaders(),
      cache: 'no-store',
    },
  );
  const payload = await parseResponse<{
    user_id: string;
    entitlements: Array<{ name: string; enabled: boolean }>;
  }>(response);
  return {
    userId: payload.user_id,
    entitlements: payload.entitlements,
  };
}

export async function updateSmartAnalysisSettings(mode: string): Promise<{ mode: string }> {
  const response = await fetch(`${getApiUrl()}/api/admin/smart-analysis/settings`, {
    method: 'PUT',
    headers: buildHeaders('application/json'),
    body: JSON.stringify({ mode }),
  });
  return parseResponse<{ mode: string }>(response);
}

export async function updateSmartAnalysisUser(
  userId: string,
  smartAnalysisEnabled: boolean,
): Promise<void> {
  const response = await fetch(
    `${getApiUrl()}/api/admin/smart-analysis/users/${encodeURIComponent(userId)}`,
    {
      method: 'PUT',
      headers: buildHeaders('application/json'),
      body: JSON.stringify({ smart_analysis_enabled: smartAnalysisEnabled }),
    },
  );
  await parseResponse(response);
}
```

- [ ] **Step 4: Add server actions and page wiring**

Modify `apps/web/app/(admin)/admin/actions.ts`:

```typescript
import {
  updateSmartAnalysisSettings,
  updateSmartAnalysisUser,
} from '../../../lib/admin-smart-analysis-api';

export async function updateSmartAnalysisModeAction(formData: FormData): Promise<void> {
  try {
    const mode = String(formData.get('mode') ?? '').trim();
    if (!mode) {
      throw new Error('mode is required');
    }

    await updateSmartAnalysisSettings(mode);
    revalidatePath('/admin');
  } catch {
    return;
  }
}

export async function updateSmartAnalysisUserAction(formData: FormData): Promise<void> {
  try {
    const userId = String(formData.get('userId') ?? '').trim();
    const enabled = String(formData.get('smartAnalysisEnabled') ?? '').trim() === 'true';
    if (!userId) {
      throw new Error('userId is required');
    }

    await updateSmartAnalysisUser(userId, enabled);
    revalidatePath(`/admin?smart_analysis_user_id=${encodeURIComponent(userId)}`);
    revalidatePath('/admin');
  } catch {
    return;
  }
}
```

Modify `apps/web/app/(admin)/admin/page.tsx` to import:

```typescript
import {
  getSmartAnalysisSettings,
  getSmartAnalysisUser,
} from '../../../lib/admin-smart-analysis-api';
```

extend `searchParams` with:

```typescript
smart_analysis_user_id?: string;
```

and load the values:

```typescript
const smartAnalysisUserId =
  resolvedSearchParams?.smart_analysis_user_id?.trim() || '';

let smartAnalysisMode = 'off';
let smartAnalysisUserEnabled = false;

try {
  const settingsPayload = await getSmartAnalysisSettings();
  smartAnalysisMode = settingsPayload.mode;
} catch {
  smartAnalysisMode = 'off';
}

if (smartAnalysisUserId) {
  try {
    const userPayload = await getSmartAnalysisUser(smartAnalysisUserId);
    smartAnalysisUserEnabled = userPayload.entitlements.some(
        (item) => item.name === 'smart_analysis' && item.enabled,
    );
  } catch {
    smartAnalysisUserEnabled = false;
  }
}
```

- [ ] **Step 5: Add a focused UI panel and shell integration**

Create `apps/web/components/admin/smart-analysis-ops-panel.tsx`:

```tsx
type SmartAnalysisOpsPanelProps = {
  mode: string;
  userId: string;
  userEnabled: boolean;
  updateModeAction: (formData: FormData) => Promise<void>;
  updateUserAction: (formData: FormData) => Promise<void>;
};

export default function SmartAnalysisOpsPanel({
  mode,
  userId,
  userEnabled,
  updateModeAction,
  updateUserAction,
}: SmartAnalysisOpsPanelProps) {
  return (
    <section aria-labelledby="smart-analysis-ops-heading">
      <h2 id="smart-analysis-ops-heading">智能分析权限运营</h2>

      <form action={updateModeAction}>
        <label>
          全局模式
          <select name="mode" defaultValue={mode}>
            <option value="off">off</option>
            <option value="gated">gated</option>
            <option value="on">on</option>
          </select>
        </label>
        <button type="submit">保存智能分析模式</button>
      </form>

      <form action="/admin" method="GET">
        <label>
          用户 ID
          <input name="smart_analysis_user_id" defaultValue={userId} />
        </label>
        <button type="submit">查询用户权益</button>
      </form>

      {userId ? (
        <div>
          <p>{userEnabled ? '当前已开通智能分析' : '当前未开通智能分析'}</p>
          <p>{userId}</p>
          <form action={updateUserAction}>
            <input type="hidden" name="userId" value={userId} />
            <input type="hidden" name="smartAnalysisEnabled" value="true" />
            <button type="submit">开通智能分析</button>
          </form>
          <form action={updateUserAction}>
            <input type="hidden" name="userId" value={userId} />
            <input type="hidden" name="smartAnalysisEnabled" value="false" />
            <button type="submit">关闭智能分析</button>
          </form>
        </div>
      ) : (
        <p>输入用户 ID 后即可查询并管理智能分析权限。</p>
      )}
    </section>
  );
}
```

Modify `apps/web/components/admin/dashboard-shell.tsx` to import:

```tsx
import SmartAnalysisOpsPanel from './smart-analysis-ops-panel';
```

extend props:

```tsx
  smartAnalysisMode?: string;
  smartAnalysisUserId?: string;
  smartAnalysisUserEnabled?: boolean;
  updateSmartAnalysisModeAction?: (formData: FormData) => Promise<void>;
  updateSmartAnalysisUserAction?: (formData: FormData) => Promise<void>;
```

and render near the top of the main content:

```tsx
      <SmartAnalysisOpsPanel
        mode={smartAnalysisMode ?? 'off'}
        userId={smartAnalysisUserId ?? ''}
        userEnabled={smartAnalysisUserEnabled ?? false}
        updateModeAction={updateSmartAnalysisModeAction ?? noopAction}
        updateUserAction={updateSmartAnalysisUserAction ?? noopAction}
      />
```

- [ ] **Step 6: Document the operator workflow**

Modify `apps/api/README.md` to add:

```md
### Admin-managed smart analysis

Smart-analysis policy now has two layers:

- a global runtime mode stored in SQLite
- a per-user `smart_analysis` entitlement stored in SQLite

Bootstrap behavior:

- if no runtime DB row exists yet, the API falls back to `GAOKAO_AGENT_SMART_ANALYSIS_MODE`

Admin operations:

- `GET /api/admin/smart-analysis/settings`
- `PUT /api/admin/smart-analysis/settings`
- `GET /api/admin/smart-analysis/users/{user_id}`
- `PUT /api/admin/smart-analysis/users/{user_id}`

During the transition phase, `metadata.entitlements` is still accepted, but admin-managed DB state is the preferred source.
```

- [ ] **Step 7: Run the focused frontend tests to verify they pass**

Run:

```powershell
pnpm --filter web test admin-page.test.tsx admin-dashboard.test.tsx
```

Expected: PASS.

- [ ] **Step 8: Run the backend regression for the touched areas**

Run:

```powershell
python -m pytest tests/test_access_control_service.py tests/test_admin_api.py tests/test_chat_services.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

Run:

```bash
git add apps/web/lib/admin-smart-analysis-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/smart-analysis-ops-panel.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx apps/api/README.md
git commit -m "feat(web): add admin smart analysis operations"
```

### Task 5: Final verification and cleanup

**Files:**
- Modify: any touched files from Tasks 1-4 if small fixes are required

- [ ] **Step 1: Run the full backend suite**

Run:

```powershell
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run the targeted web suite one more time**

Run:

```powershell
pnpm --filter web test admin-page.test.tsx admin-dashboard.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Review working tree before closeout**

Run:

```bash
git status --short
```

Expected:

- only the intended files from this plan are modified
- existing unrelated web changes remain untouched unless they were intentionally integrated

- [ ] **Step 4: Commit any final fixups**

Run:

```bash
git add apps/api/app/models/access_control.py apps/api/app/models/__init__.py apps/api/app/services/access_control.py apps/api/app/routers/admin.py apps/api/app/services/chat.py apps/api/tests/test_access_control_service.py apps/api/tests/test_admin_api.py apps/api/tests/test_chat_services.py apps/web/lib/admin-smart-analysis-api.ts apps/web/app/(admin)/admin/actions.ts apps/web/app/(admin)/admin/page.tsx apps/web/components/admin/smart-analysis-ops-panel.tsx apps/web/components/admin/dashboard-shell.tsx apps/web/tests/admin-page.test.tsx apps/web/tests/admin-dashboard.test.tsx apps/api/README.md
git commit -m "chore: polish smart analysis admin operations"
```

Only do this step if post-verification fixes were needed.
