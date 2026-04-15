export type ChatRiskFlagCopy = {
  title: string;
  description: string;
  rawKey: string;
};

const UNKNOWN_RISK_FLAG_COPY = {
  title: "\u66f4\u591a\u98ce\u9669\u63d0\u9192",
  description:
    "\u8be5\u98ce\u9669\u5df2\u8bc6\u522b\uff0c\u8be6\u7ec6\u8bf4\u660e\u5373\u5c06\u8865\u5145\u3002",
} as const;

const CHAT_RISK_FLAG_COPY: Record<string, Omit<ChatRiskFlagCopy, "rawKey">> = {
  financial_industry_competition: {
    title: "\u91d1\u878d\u884c\u4e1a\u7ade\u4e89\u98ce\u9669",
    description:
      "\u9002\u5408\u63d0\u9192\u7528\u6237\u5173\u6ce8\u91d1\u878d\u76f8\u5173\u4e13\u4e1a\u548c\u5c31\u4e1a\u65b9\u5411\u7684\u7ade\u4e89\u5f3a\u5ea6\u3002",
  },
};

export function getChatRiskFlagCopy(key: string): ChatRiskFlagCopy {
  const copy = CHAT_RISK_FLAG_COPY[key];
  if (copy) {
    return {
      ...copy,
      rawKey: key,
    };
  }

  return {
    ...UNKNOWN_RISK_FLAG_COPY,
    rawKey: key,
  };
}

export function isUnknownChatRiskFlag(key: string): boolean {
  return !(key in CHAT_RISK_FLAG_COPY);
}
