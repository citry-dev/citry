from __future__ import annotations

import asyncio
import json
import sys

from playwright.async_api import async_playwright

PROBE = r"""() => {
  const locale = "ar-EG";
  const exact = "9007199254740993.25";
  const plural = new Intl.PluralRules(locale, {
    maximumFractionDigits: 20,
  });
  const unit = new Intl.NumberFormat(locale, {
    style: "unit",
    unit: "meter",
    unitDisplay: "long",
    maximumFractionDigits: 20,
  });
  const percent = new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: 3,
  });

  return {
    userAgent: navigator.userAgent,
    unit: ["11", "11.25", "12345.67", exact].map(raw => ({
      raw,
      plural: plural.select(raw),
      formatted: unit.format(raw),
    })),
    percent: ["0.125", "12.5"].map(raw => ({
      raw,
      formatted: percent.format(raw),
    })),
  };
}"""


async def main() -> None:
    results: dict[str, object] = {}

    async with async_playwright() as playwright:
        for name in ("chromium", "firefox", "webkit"):
            browser = await getattr(playwright, name).launch()
            try:
                page = await browser.new_page()
                results[name] = await page.evaluate(PROBE)
            finally:
                await browser.close()

    sys.stdout.write(f"{json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True)}\n")


if __name__ == "__main__":
    asyncio.run(main())
