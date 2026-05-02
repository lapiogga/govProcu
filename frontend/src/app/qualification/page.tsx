/**
 * 적격심사 점수 계산기 — calc_qualification_score
 */
import { calcQualification } from "@/lib/actions";
import { extractMcpData } from "@/lib/extract";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

export default async function QualificationPage(props: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const sp = await props.searchParams;
  const hasInput = !!(sp.bid_amount && sp.base_amount);

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">적격심사 점수 계산기</h1>
        <p className="text-xs text-[var(--color-fg-muted)]">
          조달청 표준 산식. 입찰가 + 시공경험 + 기술자 + 신용등급 + 경영·기타.
        </p>
      </header>

      <Card>
        <CardContent className="p-4">
          <form action="/qualification" className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            <Field label="응찰가 (원)" name="bid_amount" defaultValue={sp.bid_amount} required />
            <Field label="기초금액 (원)" name="base_amount" defaultValue={sp.base_amount} required />
            <Select
              label="업종"
              name="biz_type"
              options={["공사", "용역", "물품"]}
              defaultValue={sp.biz_type || "공사"}
            />
            <Field label="시공경험 실적" name="experience_actual" defaultValue={sp.experience_actual} />
            <Field label="시공경험 기준" name="experience_standard" defaultValue={sp.experience_standard} />
            <Field label="기술자 수" name="tech_count" defaultValue={sp.tech_count} />
            <Field label="요구 기술자 수" name="tech_required" defaultValue={sp.tech_required} />
            <Field label="신용등급 (예: AA-)" name="credit_grade" defaultValue={sp.credit_grade} />
            <Button type="submit" className="col-span-2 lg:col-span-3">
              계산
            </Button>
          </form>
        </CardContent>
      </Card>

      {hasInput && <Result params={sp} />}
    </main>
  );
}

async function Result({ params }: { params: Record<string, string | undefined> }) {
  const r = await calcQualification({
    bid_amount: parseInt(params.bid_amount!),
    base_amount: parseInt(params.base_amount!),
    biz_type: params.biz_type || "공사",
    experience_actual: parseFloat(params.experience_actual || "0"),
    experience_standard: parseFloat(params.experience_standard || "1"),
    tech_count: parseInt(params.tech_count || "0"),
    tech_required: parseInt(params.tech_required || "1"),
    credit_grade: params.credit_grade,
  });
  if (!r.ok) {
    return (
      <Card className="border-[var(--color-danger)]">
        <CardContent className="p-4 text-sm">오류: {r.error}</CardContent>
      </Card>
    );
  }
  const data = extractMcpData<any>(r.data);
  if (!data) return <p className="text-sm">결과 없음</p>;

  const scores = data.scores || {};
  const passVariant: "success" | "warning" | "danger" =
    data.ratio_pct >= 90 ? "success" : data.ratio_pct >= 70 ? "warning" : "danger";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-baseline gap-3">
          <CardTitle>총점</CardTitle>
          <span className="font-mono text-2xl font-bold tabular-nums">
            {data.total} / {data.max_total}
          </span>
          <Badge variant={passVariant}>{data.ratio_pct}%</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-[var(--color-bg-muted)]">
            <tr>
              <th className="px-3 py-2 text-left">항목</th>
              <th className="px-3 py-2 text-right">점수</th>
              <th className="px-3 py-2 text-right">만점</th>
              <th className="px-3 py-2 text-left">상세</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(scores).map(([k, v]: any) => (
              <tr key={k} className="border-t">
                <td className="px-3 py-2 font-medium">{labelMap[k] || k}</td>
                <td className="px-3 py-2 text-right tabular-nums">{v.score}</td>
                <td className="px-3 py-2 text-right tabular-nums text-[var(--color-fg-muted)]">
                  {v.max}
                </td>
                <td className="px-3 py-2 text-xs text-[var(--color-fg-muted)]">
                  {summarizeDetail(v.detail)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="border-t px-4 py-3 text-xs text-[var(--color-fg-muted)]">
          {data.note}
        </p>
      </CardContent>
    </Card>
  );
}

const labelMap: Record<string, string> = {
  bid_price: "입찰가격",
  experience: "시공경험",
  tech_capability: "기술능력",
  credit: "신용평가",
  management: "경영상태",
  etc: "기타",
};

function summarizeDetail(detail: any): string {
  if (!detail) return "";
  if (detail.bid_rate_pct != null)
    return `입찰률 ${detail.bid_rate_pct}% / 하한 ${detail.lower_rate_pct}% [${detail.status}]`;
  if (detail.ratio_pct != null) return `${detail.ratio_pct}% 충족`;
  if (detail.grade) return `${detail.grade} (반영 ${(detail.ratio * 100).toFixed(0)}%)`;
  return JSON.stringify(detail).slice(0, 80);
}

function Field({
  label,
  name,
  defaultValue,
  required,
}: {
  label: string;
  name: string;
  defaultValue?: string;
  required?: boolean;
}) {
  return (
    <div className="space-y-1">
      <Label htmlFor={name} className="text-xs text-[var(--color-fg-muted)]">
        {label}
      </Label>
      <Input
        id={name}
        name={name}
        defaultValue={defaultValue}
        required={required}
      />
    </div>
  );
}

function Select({
  label,
  name,
  options,
  defaultValue,
}: {
  label: string;
  name: string;
  options: string[];
  defaultValue?: string;
}) {
  return (
    <div className="space-y-1">
      <Label htmlFor={name} className="text-xs text-[var(--color-fg-muted)]">
        {label}
      </Label>
      <select
        id={name}
        name={name}
        defaultValue={defaultValue}
        className="flex h-9 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}
