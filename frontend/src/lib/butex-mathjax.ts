"use client";

/**
 * تهيئة MathJax + تسجيل BuTeX مرة واحدة (عقد التكامل من README الحزمة):
 * 1. ضبط window.MathJax قبل تحميل tex-svg.js
 * 2. registerBuTeX قبل defaultReady، وregisterBuTeXSvgTextWrapper بعده
 * 3. حقن أنماط BuTeX وأنماط محرر المستندات v2
 */

const MATHJAX_SRC = "https://cdn.jsdelivr.net/npm/mathjax@4.1/tex-svg.js";

let bootPromise: Promise<void> | null = null;

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`تعذّر تحميل ${src}`));
    document.head.appendChild(script);
  });
}

export function ensureButexMathJax(): Promise<void> {
  if (bootPromise) return bootPromise;

  bootPromise = (async () => {
    const [butex, reactDocument2] = await Promise.all([
      import("@drghaliasri/butex"),
      import("@drghaliasri/butex/react-document2"),
    ]);

    reactDocument2.injectBuTeXDocument2Styles(document);

    const win = window as unknown as {
      MathJax?: { startup?: { promise?: Promise<unknown> } };
    };

    if (!win.MathJax?.startup?.promise) {
      win.MathJax = {
        tex: {
          packages: { "[+]": ["ams", butex.BUTEX_TEX_PACKAGE] },
        },
        startup: {
          ready: () => {
            const mathJax = win.MathJax as unknown as Parameters<
              typeof butex.registerBuTeX
            >[0] & { startup: { defaultReady: () => void } };
            butex.registerBuTeX(mathJax);
            butex.injectBuTeXStyles();
            mathJax.startup.defaultReady();
            butex.registerBuTeXSvgTextWrapper(mathJax);
          },
        },
      } as typeof win.MathJax;

      // MathJax لا يُجمَّع عبر webpack — يُحمَّل كسكربت في المتصفح
      await loadScript(MATHJAX_SRC);
    }

    await win.MathJax?.startup?.promise;
  })();

  return bootPromise;
}
