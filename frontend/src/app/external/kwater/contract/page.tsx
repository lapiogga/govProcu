/**
 * K-water 계약 단건 상세 — /external/kwater 의 row 클릭 진입.
 *
 * 5/3 N43 — KWater 자체 API 가 ordgNo 단건 검색 미지원이라 query params 로 row 데이터 전달.
 * 동일 ordgNo 의 contract 정보를 raw 형태로 표시 + KWater 자체 시스템 외부 링크.
 */
import Link from "next/link";
import { fmtWon, fmtDate } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default async function KwaterContractDetailPage(props: {
  searchParams: Promise<{
    no?: string;
    dt?: string;
    title?: string;
    dept?: string;
    biz?: string;
    winner?: string;
    method?: string;
    limit?: string;
    amount?: string;
    p_from?: string;
    p_to?: string;
  }>;
}) {
  const sp = await props.searchParams;
  const no = sp.no || "";
  const winnerName = sp.winner || "";

  if (!no) {
    return (
      <main className="space-y-4">
        <header>
          <h1 className="text-2xl font-semibold">계약 상세</h1>
        </header>
        <Card>
          <CardContent className="p-4 text-sm text-[var(--color-fg-muted)]">
            계약번호 미지정. /external/kwater 에서 row 를 클릭하세요.
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="space-y-4">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{sp.title || no}</h1>
          <p className="text-xs text-[var(--color-fg-muted)]">
            한국수자원공사 전자조달 계약 단건 — ordgNo {no}
          </p>
        </div>
        <Link href="/external/kwater">
          <Button variant="outline" size="sm">
            ← 목록
          </Button>
        </Link>
      </header>

      <Card>
        <CardContent className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2">
          <Field label="계약번호" mono value={no} />
          <Field label="계약일자" value={fmtDate(sp.dt)} />
          <Field label="제목" value={sp.title || "—"} className="md:col-span-2" />
          <Field label="계약부서" value={sp.dept || "—"} />
          <Field
            label="업종"
            value={
              <Badge
                variant={
                  sp.biz === "용역"
                    ? "default"
                    : sp.biz === "공사"
                      ? "secondary"
                      : "outline"
                }
              >
                {sp.biz || "—"}
              </Badge>
            }
          />
          <Field
            label="계약업체"
            value={
              winnerName ? (
                <Link
                  href={`/vendors?name=${encodeURIComponent(winnerName)}`}
                  className="entity-link font-medium"
                  title={`업체 LIKE 검색: ${winnerName}`}
                >
                  {winnerName}
                </Link>
              ) : (
                "—"
              )
            }
          />
          <Field
            label="계약방법"
            value={
              <span>
                {sp.method || "—"}
                {sp.limit && sp.limit !== "-" && (
                  <span className="ml-1 text-xs text-[var(--color-fg-muted)]">
                    ({sp.limit})
                  </span>
                )}
              </span>
            }
          />
          <Field
            label="계약금액"
            value={
              <span className="tabular-nums font-medium">
                {sp.amount ? fmtWon(parseInt(sp.amount, 10)) : "—"}
              </span>
            }
          />
          <Field
            label="이행기간"
            value={
              sp.p_from || sp.p_to ? (
                <span className="text-xs tabular-nums">
                  {fmtDate(sp.p_from)} ~ {fmtDate(sp.p_to)}
                </span>
              ) : (
                "—"
              )
            }
            className="md:col-span-2"
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-2 p-4 text-xs text-[var(--color-fg-muted)]">
          <p>
            출처: K-water 전자조달 OpenAPI (apis.data.go.kr/B500001/ebid/cntrct3)
          </p>
          <p>
            <a
              href="https://ebid.kwater.or.kr/"
              target="_blank"
              rel="noreferrer"
              className="entity-link"
            >
              K-water 전자조달시스템 (ebid.kwater.or.kr) ↗
            </a>
            {" — "}
            ordgNo {no} 직접 조회는 외부 시스템 검색에서.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

function Field({
  label,
  value,
  mono,
  className,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  className?: string;
}) {
  return (
    <div className={className}>
      <div className="text-xs text-[var(--color-fg-muted)]">{label}</div>
      <div className={mono ? "font-mono text-sm" : "text-sm"}>{value}</div>
    </div>
  );
}
