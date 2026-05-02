"use client";

/**
 * 3 테마 모드 토글 — system(아이보리 파스텔, default) / light(순백) / dark.
 *
 * 동작:
 *  - localStorage 'govprocu.theme' 에 저장
 *  - <html data-theme="..."> 속성 갱신 → globals.css 의 CSS 변수 적용
 *  - 페이지 로드 시 setThemeFromStorage 가 깜빡임 방지 (layout 의 inline script 와 페어)
 */
import { useEffect, useState } from "react";

type Theme = "system" | "light" | "dark";

const KEY = "govprocu.theme";

const LABEL: Record<Theme, string> = {
  system: "🎨 아이보리",
  light: "☀ 라이트",
  dark: "🌙 다크",
};

function applyTheme(t: Theme) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", t);
  try {
    localStorage.setItem(KEY, t);
  } catch {
    /* 시크릿 모드 등 storage 차단 — silently ignore */
  }
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY) as Theme | null;
      if (saved && ["system", "light", "dark"].includes(saved)) {
        setTheme(saved);
        applyTheme(saved);
      }
    } catch {
      /* noop */
    }
  }, []);

  function pick(next: Theme) {
    setTheme(next);
    applyTheme(next);
  }

  return (
    <div
      role="radiogroup"
      aria-label="테마 모드"
      className="inline-flex items-center gap-1 rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] p-1 text-xs"
    >
      {(Object.keys(LABEL) as Theme[]).map((k) => (
        <button
          key={k}
          type="button"
          role="radio"
          aria-checked={theme === k}
          onClick={() => pick(k)}
          className={`rounded px-2 py-1 transition-colors ${
            theme === k
              ? "bg-[var(--color-primary)] text-[var(--color-primary-fg)]"
              : "hover:bg-[var(--color-bg-muted)]"
          }`}
        >
          {LABEL[k]}
        </button>
      ))}
    </div>
  );
}

/**
 * SSR-safe inline script — layout <head> 에 삽입해 first-paint 에 테마 적용.
 * (저장된 테마 != system 일 때 페이지 깜빡임 방지)
 */
export const themeBootstrapScript = `
(function(){try{var t=localStorage.getItem('${KEY}');if(t&&['system','light','dark'].indexOf(t)>=0){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();
`;
