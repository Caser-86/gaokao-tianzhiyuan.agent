import { expect, test } from 'vitest';

import { getPlatformEntitlementCopy } from '../lib/platform-entitlement-labels';

test('returns user-facing copy for a known entitlement key', () => {
  expect(getPlatformEntitlementCopy('school_basic_access')).toEqual({
    title: '院校基础信息查看',
    description: '查看院校的基础介绍、招生范围和核心数据。',
    rawKey: 'school_basic_access',
  });
});

test('returns fallback copy and preserves the raw key for unknown entitlements', () => {
  expect(getPlatformEntitlementCopy('future_capability')).toEqual({
    title: '更多平台能力',
    description: '该能力已开通，详细说明即将补充。',
    rawKey: 'future_capability',
  });
});
