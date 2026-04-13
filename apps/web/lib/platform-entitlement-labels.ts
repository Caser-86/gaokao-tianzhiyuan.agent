export type PlatformEntitlementCopy = {
  title: string;
  description: string;
  rawKey: string;
};

const UNKNOWN_ENTITLEMENT_COPY = {
  title: '\u66f4\u591a\u5e73\u53f0\u80fd\u529b',
  description:
    '\u8be5\u80fd\u529b\u5df2\u5f00\u901a\uff0c\u8be6\u7ec6\u8bf4\u660e\u5373\u5c06\u8865\u5145\u3002',
} as const;

const ENTITLEMENT_COPY: Record<string, Omit<PlatformEntitlementCopy, 'rawKey'>> = {
  school_basic_access: {
    title: '\u9662\u6821\u57fa\u7840\u4fe1\u606f\u67e5\u770b',
    description:
      '\u67e5\u770b\u9662\u6821\u7684\u57fa\u7840\u4ecb\u7ecd\u3001\u62db\u751f\u8303\u56f4\u548c\u6838\u5fc3\u6570\u636e\u3002',
  },
  major_basic_access: {
    title: '\u4e13\u4e1a\u57fa\u7840\u4fe1\u606f\u67e5\u770b',
    description:
      '\u67e5\u770b\u4e13\u4e1a\u7684\u57f9\u517b\u65b9\u5411\u3001\u9009\u79d1\u8981\u6c42\u548c\u57fa\u7840\u89e3\u8bfb\u3002',
  },
  risk_alert_access: {
    title: '\u98ce\u9669\u63d0\u9192',
    description:
      '\u83b7\u5f97\u5fd7\u613f\u586b\u62a5\u4e2d\u7684\u6ce2\u52a8\u63d0\u9192\u548c\u98ce\u9669\u63d0\u793a\u3002',
  },
  school_deep_dive_access: {
    title: '\u9662\u6821\u6df1\u5ea6\u5206\u6790',
    description:
      '\u67e5\u770b\u9662\u6821\u5206\u6570\u8d8b\u52bf\u3001\u5f55\u53d6\u5c42\u6b21\u548c\u6df1\u5ea6\u89e3\u8bfb\u3002',
  },
  major_deep_dive_access: {
    title: '\u4e13\u4e1a\u6df1\u5ea6\u5206\u6790',
    description:
      '\u67e5\u770b\u4e13\u4e1a\u524d\u666f\u3001\u8bfe\u7a0b\u7ed3\u6784\u548c\u7ade\u4e89\u60c5\u51b5\u5206\u6790\u3002',
  },
  region_compare_access: {
    title: '\u5730\u533a\u5bf9\u6bd4\u5206\u6790',
    description:
      '\u5bf9\u6bd4\u4e0d\u540c\u5730\u533a\u7684\u9662\u6821\u673a\u4f1a\u3001\u5f55\u53d6\u96be\u5ea6\u548c\u9009\u62e9\u7a7a\u95f4\u3002',
  },
};

export function getPlatformEntitlementCopy(key: string): PlatformEntitlementCopy {
  const copy = ENTITLEMENT_COPY[key];

  if (copy) {
    return {
      ...copy,
      rawKey: key,
    };
  }

  return {
    ...UNKNOWN_ENTITLEMENT_COPY,
    rawKey: key,
  };
}

export function isUnknownPlatformEntitlement(key: string): boolean {
  return !(key in ENTITLEMENT_COPY);
}
