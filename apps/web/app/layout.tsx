import './globals.css';

import type { ReactNode } from 'react';

export const metadata = {
  title: '高考志愿助手',
  description: '面向考生和家长的学校、专业、地域与就业查询助手。',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
