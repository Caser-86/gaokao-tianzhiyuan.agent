import type { AdminSmartAnalysisMode } from '../../lib/admin-smart-analysis-api';

type SmartAnalysisOpsPanelProps = {
  mode: AdminSmartAnalysisMode;
  userId?: string;
  userEnabled: boolean;
  updateModeAction: (formData: FormData) => Promise<void>;
  updateUserAction: (formData: FormData) => Promise<void>;
};

const modeOptions: Array<{ value: AdminSmartAnalysisMode; label: string }> = [
  { value: 'off', label: '全关' },
  { value: 'gated', label: '部分开' },
  { value: 'on', label: '全开' },
];

export default function SmartAnalysisOpsPanel({
  mode,
  userId,
  userEnabled,
  updateModeAction,
  updateUserAction,
}: SmartAnalysisOpsPanelProps) {
  const normalizedUserId = userId?.trim() ?? '';

  return (
    <section aria-labelledby="smart-analysis-ops-heading">
      <h2 id="smart-analysis-ops-heading">智能分析权限运营</h2>
      <p>支持全局模式切换，也支持按用户开通或关闭智能分析。</p>

      <form action={updateModeAction}>
        <label>
          全局模式
          <select name="mode" defaultValue={mode}>
            {modeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.value}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">保存智能分析模式</button>
      </form>

      <form action="/admin" method="GET">
        <label>
          用户 ID
          <input
            type="text"
            name="smart_analysis_user_id"
            defaultValue={normalizedUserId}
            placeholder="输入公众号 openid 或其他用户标识"
          />
        </label>
        <button type="submit">查询用户权益</button>
      </form>

      {normalizedUserId ? (
        <div>
          <p>{`当前用户：${normalizedUserId}`}</p>
          <p>{userEnabled ? '当前已开通智能分析' : '当前未开通智能分析'}</p>

          <form action={updateUserAction}>
            <input type="hidden" name="userId" value={normalizedUserId} />
            <input type="hidden" name="enabled" value="true" />
            <button type="submit">开通智能分析</button>
          </form>

          <form action={updateUserAction}>
            <input type="hidden" name="userId" value={normalizedUserId} />
            <input type="hidden" name="enabled" value="false" />
            <button type="submit">关闭智能分析</button>
          </form>
        </div>
      ) : (
        <p>输入用户 ID 后可查询并调整该用户的智能分析权益。</p>
      )}
    </section>
  );
}
