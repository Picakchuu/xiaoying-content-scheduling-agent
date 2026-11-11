"""Collect actual evidence into one reviewer-facing document without model calls."""
import json
from pathlib import Path


def main():
    root=Path('examples')
    cases=[p for p in root.iterdir() if p.is_dir() and (p/'input.json').exists()]
    cases+=sorted((root/'real').glob('*/*/input.json'))
    cases=[p.parent if p.is_file() else p for p in cases]
    cases+=list((root/'real-replanning').glob('*/')) if (root/'real-replanning').exists() else []
    lines=['# 集中验收报告','', '由 `python scripts/build_acceptance_report.py` 从实际文件汇总。输入、输出摘要与关键Trace集中展示，原始输出保留链接。Mock仅证明流程；real表示实际模型动作决策，本地业务工具仍使用合成资料与模板。','']
    for folder in cases:
        if not (folder/'input.json').exists():
            continue
        raw=json.loads((folder/'input.json').read_text(encoding='utf-8'))
        out=json.loads((folder/'output.json').read_text(encoding='utf-8'))
        name=folder.relative_to(root).as_posix()
        summary={k:out[k] for k in ('mode','model','status','reason','missing','errors','total_cost','actual_tool_cost','saved_plan_id','replayed') if k in out}
        lines += ['## '+name,'','输入：','```json',json.dumps(raw,ensure_ascii=False,indent=2),'```','实际输出摘要：','```json',json.dumps(summary,ensure_ascii=False,indent=2),'```',
                  f'[完整输出]({name}/output.json) · [原始Trace]({name}/trace.jsonl)','', '| 步骤 | 动作与参数 | 实际观察摘要 | 后续动作 | 简要依据 |','|---|---|---|---|---|']
        for step in out.get('trace',[]):
            obs=step['observation'];data=obs.get('data',{})
            brief={k:data[k] for k in ('total_cost','budget_gap','feasible','variant','plan_id') if k in data}
            if not brief: brief={'ok':obs.get('ok'),'error':obs.get('error_code'),'summary':obs.get('summary','')[:160]}
            cells=[str(step['step']),step['action']+' '+json.dumps(step['args'],ensure_ascii=False),json.dumps(brief,ensure_ascii=False),step['next_action'],step['rationale']]
            lines.append('| '+' | '.join(c.replace('|','/').replace('\n',' ') for c in cells)+' |')
        if not out.get('trace'): lines.append('| — | 无工具执行 | 输入校验或身份检查已结束 | end | 见实际输出 |')
        lines.append('')
    lines+=['## 对话补充证据','', '[真实追问、相对日期与文件输入](chat-live/7ac3833462c8/conversation.json)。对话日志包含用户原话与中文回复，完整执行结果同目录保存。','',
            '## 验收边界','', '失败终态手动续跑未实现，属于加分项。脚本分镜为本地模板；业务费用为模拟单位。真实样本量小，不代表总体成功率。个人实际用时和贡献由候选人填写，提交SHA使用git rev-parse HEAD取得。']
    (root/'acceptance-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
