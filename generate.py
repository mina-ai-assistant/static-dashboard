#!/usr/bin/env python3

from __future__ import annotations

import json
import argparse
import sys
import urllib.parse
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def normalize(data: dict[str, Any]) -> dict[str, Any]:
    categories = data.get("categories")
    if not isinstance(categories, list):
        raise ValueError("Expected top-level 'categories' list in source YAML")

    normalized_categories: list[dict[str, Any]] = []
    total_items = 0

    for category in categories:
        if not isinstance(category, dict):
            raise ValueError("Each category must be a mapping")

        name = str(category.get("name", "")).strip()
        if not name:
            raise ValueError("Each category requires a non-empty 'name'")

        icon = str(category.get("icon") or "lucide:folder").strip()
        items = category.get("items")
        if not isinstance(items, list):
            raise ValueError(f"Category '{name}' requires an 'items' list")

        normalized_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Category '{name}' contains an invalid item")

            item_name = str(item.get("name", "")).strip()
            item_url = str(item.get("url", "")).strip()
            if not item_name or not item_url:
                raise ValueError(f"Each item in '{name}' requires 'name' and 'url'")

            tags = item.get("tags") or []
            if not isinstance(tags, list):
                raise ValueError(f"Item '{item_name}' in '{name}' has invalid 'tags'")

            icon_name = str(item.get("icon") or "lucide:link").strip()
            search_blob = " ".join(
                [
                    name,
                    item_name,
                    item_url,
                    " ".join(str(tag).strip() for tag in tags if str(tag).strip()),
                ]
            ).lower()

            normalized_items.append(
                {
                    "name": item_name,
                    "url": item_url,
                    "icon": icon_name,
                    "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
                    "searchText": search_blob,
                }
            )

        total_items += len(normalized_items)
        normalized_categories.append(
            {
                "name": name,
                "icon": icon,
                "itemCount": len(normalized_items),
                "items": normalized_items,
            }
        )

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "categoryCount": len(normalized_categories),
        "itemCount": total_items,
        "categories": normalized_categories,
    }


def json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def favicon_data_uri() -> str:
    svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#0b0f17'/>
      <stop offset='100%' stop-color='#111827'/>
    </linearGradient>
    <linearGradient id='accent' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#f472b6'/>
      <stop offset='100%' stop-color='#ec4899'/>
    </linearGradient>
  </defs>
  <rect x='4' y='4' width='56' height='56' rx='14' fill='url(#bg)'/>
  <path d='M19 22 L29 32 L19 42' fill='none' stroke='url(#accent)' stroke-width='5' stroke-linecap='round' stroke-linejoin='round'/>
  <rect x='33' y='38' width='14' height='4.5' rx='2.25' fill='url(#accent)'/>
</svg>"""
    return "data:image/svg+xml," + urllib.parse.quote(svg)


def build_html(data: dict[str, Any]) -> str:
    title = "Dashboard"
    payload = json_for_script(data)
    favicon = favicon_data_uri()
    generated_dt = datetime.fromisoformat(data["generatedAt"])
    display_dt = generated_dt.astimezone(ZoneInfo("Europe/Amsterdam"))
    generated_at = escape(data["generatedAt"])
    generated_time = escape(display_dt.strftime("%H:%M"))
    generated_date = escape(display_dt.strftime("%d-%m-%Y"))

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="icon" href="{favicon}" type="image/svg+xml">
    <meta name="description" content="Bookmark dashboard generated from YAML.">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
      tailwind.config = {{
        theme: {{
          extend: {{
            fontFamily: {{
              sans: ['\"Inter\"', 'Avenir Next', 'Segoe UI', 'ui-sans-serif', 'system-ui', 'sans-serif']
            }},
            colors: {{
              slate: {{
                950: '#090c12'
              }}
            }}
          }}
        }}
      }};
    </script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script defer src="https://code.iconify.design/3/3.1.1/iconify.min.js"></script>
    <style>
      :root {{
        color-scheme: light dark;
        --bg-base: #f8fafc;
        --bg-deep: #f1f5f9;
        --bg-surface: rgba(255, 255, 255, 0.6);
        --bg-surface-border: rgba(15, 23, 42, 0.08);
        --bg-orb-violet: rgba(139, 92, 246, 0.15);
        --bg-orb-fuchsia: rgba(236, 72, 153, 0.1);
        --vignette-start: rgba(248, 250, 252, 0.08);
        --vignette-end: rgba(248, 250, 252, 0.52);
        --shadow-color: rgba(15, 23, 42, 0.08);
        --tag-chip-bg: rgba(241, 245, 249, 0.7);
        --tag-chip-border: rgba(139, 92, 246, 0.2);
      }}
      @media (prefers-color-scheme: dark) {{
        :root {{
          --bg-base: #070b12;
          --bg-deep: #0b1020;
          --bg-surface: rgba(12, 18, 28, 0.42);
          --bg-surface-border: rgba(148, 163, 184, 0.14);
          --bg-orb-violet: rgba(139, 92, 246, 0.20);
          --bg-orb-fuchsia: rgba(236, 72, 153, 0.14);
          --vignette-start: rgba(7, 11, 18, 0.08);
          --vignette-end: rgba(7, 11, 18, 0.52);
          --shadow-color: rgba(3, 7, 18, 0.28);
          --tag-chip-bg: rgba(31, 41, 55, 0.55);
          --tag-chip-border: rgba(139, 92, 246, 0.16);
        }}
      }}
      body {{
        background:
          radial-gradient(circle at 85% 0%, rgba(168, 85, 247, 0.08), transparent 24%),
          linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-base) 100%);
        overflow-x: hidden;
      }}
      body::before {{
        position: fixed;
        inset: -20%;
        background:
          radial-gradient(circle at 82% 10%, rgba(168, 85, 247, 0.14), transparent 30%),
          radial-gradient(circle at 54% 12%, rgba(236, 72, 153, 0.12), transparent 26%);
        filter: blur(72px);
        pointer-events: none;
        transform-origin: center;
        transform: translate3d(0, 0, 0) scale(1) rotate(0deg);
        opacity: 0.64;
        content: "";
      }}
      body::after {{
        position: fixed;
        inset: 0;
        background:
          radial-gradient(circle at center, transparent 0%, var(--vignette-start) 52%, var(--vignette-end) 100%);
        pointer-events: none;
        content: "";
      }}
      .ambient {{
        position: fixed;
        inset: 0;
        overflow: hidden;
        pointer-events: none;
        transform: translate3d(0, 0, 0);
      }}
      .ambient__aurora {{
        position: absolute;
        inset: -20% -10%;
        background:
          radial-gradient(circle at 78% 26%, rgba(168, 85, 247, 0.16), transparent 18%);
        filter: blur(58px);
        transform-origin: center;
        transform: translate3d(0, 0, 0) rotate(0deg) scale(0.98);
        opacity: 0.4;
      }}
      .ambient__orb {{
        position: absolute;
        border-radius: 9999px;
        filter: blur(96px);
        mix-blend-mode: screen;
        opacity: 1;
      }}
      .ambient__orb--two {{
        top: 18%;
        right: -12rem;
        width: 38rem;
        height: 38rem;
        background:
          radial-gradient(circle at 40% 35%, var(--bg-orb-violet), transparent 56%),
          radial-gradient(circle at 65% 60%, var(--bg-orb-fuchsia), transparent 62%);
        transform: translate3d(0, 0, 0) scale(0.98);
        opacity: 0.42;
      }}
      .ambient__orb--three {{
        top: -8rem;
        bottom: auto;
        left: 42%;
        right: auto;
        width: 24rem;
        height: 24rem;
        background:
          radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.12), transparent 50%),
          radial-gradient(circle at 35% 35%, rgba(168, 85, 247, 0.06), transparent 60%);
        transform: translate3d(0, 0, 0) scale(0.98);
        opacity: 0.34;
      }}
      .ambient__beam--secondary {{
        top: -4%;
        bottom: auto;
        left: 55%;
        width: min(44vw, 34rem);
        height: 24rem;
        background:
          radial-gradient(circle at 50% 45%, rgba(244, 63, 94, 0.18), transparent 34%),
          radial-gradient(circle at 58% 55%, rgba(236, 72, 153, 0.16), transparent 42%),
          radial-gradient(circle at 44% 65%, rgba(168, 85, 247, 0.08), transparent 52%);
        filter: blur(150px);
        opacity: 0.12;
        transform: translateX(-50%) translateY(0) rotate(2deg) scale(1);
      }}
      main {{
        position: relative;
        z-index: 1;
      }}
      .surface {{
        background: var(--bg-surface);
        backdrop-filter: blur(18px);
        border: 1px solid var(--bg-surface-border);
        box-shadow:
          inset 0 1px 0 rgba(255, 255, 255, 0.05),
          0 18px 60px var(--shadow-color);
      }}
      .surface-soft {{
        background: transparent;
        border: 0;
      }}
      .tag-chip {{
        background: var(--tag-chip-bg);
        border: 1px solid var(--tag-chip-border);
      }}
      .section-grid {{
        display: flex;
        justify-content: center;
        align-items: flex-start;
        gap: 1.25rem;
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
      }}
      .section-column {{
        display: grid;
        align-content: start;
        gap: 1.25rem;
        flex: 0 0 auto;
        width: 100%;
        max-width: 100%;
        min-width: 0;
      }}
      .category-card {{
        width: 100%;
        min-width: 0;
        box-sizing: border-box;
      }}
      .bookmark-list {{
        display: grid;
        gap: 0.35rem;
      }}
      [x-cloak] {{
        display: none !important;
      }}
    </style>
  </head>
  <body class="min-h-screen text-slate-800 dark:text-slate-100 antialiased">
    <div class="ambient" aria-hidden="true">
      <div class="ambient__aurora"></div>
      <div class="ambient__beam ambient__beam--secondary"></div>
      <div class="ambient__orb ambient__orb--two"></div>
      <div class="ambient__orb ambient__orb--three"></div>
    </div>
    <script id="dashboard-data" type="application/json">{payload}</script>
    <main
      x-data="dashboardApp()"
      x-init="init()"
      class="mx-auto min-h-screen w-full px-4 py-8 sm:px-6 lg:px-8"
    >
      <header class="mx-auto max-w-3xl text-center">
        <h1 class="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white sm:text-3xl">Dashboard</h1>
        <div class="mt-2 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
          <span><span class="text-cyan-600 dark:text-cyan-300" x-text="totalItemCount"></span> bookmarks</span>
          <span><span class="text-fuchsia-600 dark:text-fuchsia-300" x-text="categoryCount"></span> categories</span>
          <template x-if="query">
            <span><span class="text-violet-600 dark:text-violet-300" x-text="visibleItemCount"></span> shown</span>
          </template>
        </div>
      </header>

      <section class="mx-auto mt-8 max-w-2xl">
        <label class="flex items-center gap-3 border-b border-slate-300 dark:border-slate-800 px-4 py-3 transition focus-within:border-fuchsia-500/70 dark:focus-within:border-fuchsia-500/70">
          <span class="iconify text-lg text-fuchsia-600/80 dark:text-fuchsia-400/80" data-icon="lucide:search"></span>
          <input
            x-ref="search"
            x-model="query"
            type="search"
            placeholder="Search"
            class="w-full border-0 bg-transparent text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-0 sm:text-base"
            autocomplete="off"
            spellcheck="false"
          >
          <kbd class="hidden rounded-md border border-violet-500/20 bg-slate-100 dark:bg-slate-900/80 px-2 py-1 text-xs text-slate-400 dark:text-slate-500 sm:block">/</kbd>
        </label>
      </section>

      <section x-ref="categorySection" class="mx-auto mt-12 w-full" x-show="visibleItemCount > 0" x-cloak>
        <div class="section-grid" :style="masonryGridStyle">
          <template x-for="(column, columnIndex) in masonryColumns" :key="`column-${{columnIndex}}`">
            <div class="section-column" :style="masonryColumnStyle">
              <template x-for="category in column" :key="category.name">
                <section class="surface category-card rounded-2xl px-5 py-4">
                  <div class="mb-4 flex items-center justify-between gap-3 border-b border-violet-500/10 pb-3">
                    <div class="flex min-w-0 items-center gap-3">
                      <span class="iconify shrink-0 text-base text-fuchsia-600/80 dark:text-fuchsia-400/80" :data-icon="category.icon"></span>
                      <h2 class="truncate text-sm font-medium text-slate-800 dark:text-slate-200" x-text="category.name"></h2>
                    </div>
                    <span class="text-[11px] text-slate-500 dark:text-slate-600" x-text="category.items.length"></span>
                  </div>
                  <div class="bookmark-list">
                    <template x-for="item in category.items" :key="item.url">
                      <a
                        :href="item.url"
                        target="_blank"
                        rel="noreferrer noopener"
                        class="group box-border flex w-full min-w-0 items-start gap-4 rounded-xl px-3 py-3 transition hover:bg-fuchsia-500/[0.05]"
                      >
                        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-900/85 text-cyan-600 dark:text-cyan-300/80 transition group-hover:text-cyan-700 dark:group-hover:text-cyan-200">
                          <span class="iconify text-xl" :data-icon="item.icon"></span>
                        </div>
                        <div class="min-w-0 flex-1">
                          <div class="flex items-center gap-2">
                            <h3 class="truncate text-sm font-medium text-slate-900 dark:text-white" x-text="item.name"></h3>
                            <span class="iconify shrink-0 text-slate-400 dark:text-slate-700 transition group-hover:text-fuchsia-600 dark:group-hover:text-fuchsia-300" data-icon="lucide:arrow-up-right"></span>
                          </div>
                          <p class="mt-1 max-w-[34ch] truncate text-xs text-slate-500" x-text="item.url"></p>
                          <div class="mt-2 flex flex-wrap gap-2" x-show="item.tags.length">
                            <template x-for="tag in item.tags" :key="tag">
                              <span class="tag-chip inline-block rounded px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-slate-600 dark:text-slate-300" x-text="tag"></span>
                            </template>
                          </div>
                        </div>
                      </a>
                    </template>
                  </div>
                </section>
              </template>
            </div>
          </template>
        </div>
      </section>

      <section
        x-show="visibleItemCount === 0"
        x-cloak
        class="mx-auto mt-14 max-w-2xl text-center"
      >
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-900/80 text-slate-500">
          <span class="iconify text-2xl" data-icon="lucide:search-x"></span>
        </div>
        <h2 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">No matches</h2>
        <p class="mt-2 text-sm text-slate-500">Try another search term.</p>
      </section>

      <footer class="mt-10 text-center text-[10px] text-slate-500">
        <time datetime="{generated_at}">Dashboard: {generated_time} {generated_date}</time>
      </footer>
    </main>

    <script>
      function dashboardApp() {{
        const data = JSON.parse(document.getElementById('dashboard-data').textContent);
        return {{
          query: '',
          categories: data.categories,
          layoutWidth: 0,
          masonryColumnWidth: 350,
          masonryGap: 20,
          totalItemCount: data.itemCount,
          categoryCount: data.categoryCount,
          init() {{
            const updateLayoutWidth = () => {{
              if (this.$refs.categorySection) {{
                this.layoutWidth = this.$refs.categorySection.clientWidth;
              }}
            }};

            updateLayoutWidth();

            if ('ResizeObserver' in window && this.$refs.categorySection) {{
              const observer = new ResizeObserver(() => updateLayoutWidth());
              observer.observe(this.$refs.categorySection);
            }} else {{
              window.addEventListener('resize', updateLayoutWidth);
            }}

            window.addEventListener('keydown', (event) => {{
              const target = event.target;
              const typingInField = target && (
                target.tagName === 'INPUT' ||
                target.tagName === 'TEXTAREA' ||
                target.isContentEditable
              );

              if (event.key === '/' && !typingInField) {{
                event.preventDefault();
                this.$refs.search.focus();
                this.$refs.search.select();
              }}

              if (event.key === 'Enter' && this.visibleItemCount > 0 && !event.metaKey && !event.ctrlKey) {{
                if (typingInField || target === document.body) {{
                  event.preventDefault();
                  this.openFirstVisible();
                }}
              }}
            }});
          }},
          get normalizedQuery() {{
            return this.query.trim().toLowerCase();
          }},
          get filteredCategories() {{
            const query = this.normalizedQuery;
            return this.categories
              .map((category) => {{
                const items = !query
                  ? category.items
                  : category.items.filter((item) => item.searchText.includes(query));
                return {{
                  ...category,
                  items,
                }};
              }})
              .filter((category) => category.items.length > 0);
          }},
          get visibleItemCount() {{
            return this.filteredCategories.reduce((count, category) => count + category.items.length, 0);
          }},
          get masonryRenderedColumnWidth() {{
            const availableWidth = this.layoutWidth || window.innerWidth || this.masonryColumnWidth;

            if (this.masonryColumnCount <= 1) {{
              return Math.min(availableWidth, this.masonryColumnWidth);
            }}

            return this.masonryColumnWidth;
          }},
          get masonryGridStyle() {{
            const columnCount = this.masonryColumnCount;

            if (columnCount <= 0) {{
              return '';
            }}

            const gridWidth = (columnCount * this.masonryRenderedColumnWidth) + ((columnCount - 1) * this.masonryGap);
            return `width: min(100%, ${{gridWidth}}px);`;
          }},
          get masonryColumnStyle() {{
            const columnWidth = this.masonryRenderedColumnWidth;

            if (columnWidth <= 0) {{
              return '';
            }}

            return `flex-basis: ${{columnWidth}}px; width: min(100%, ${{columnWidth}}px);`;
          }},
          get masonryColumnCount() {{
            const categoryCount = this.filteredCategories.length;

            if (categoryCount <= 1) {{
              return categoryCount;
            }}

            const availableWidth = this.layoutWidth || window.innerWidth || this.masonryColumnWidth;
            const columnCount = Math.floor((availableWidth + this.masonryGap) / (this.masonryColumnWidth + this.masonryGap));

            return Math.max(1, Math.min(categoryCount, columnCount));
          }},
          get masonryColumns() {{
            const columnCount = this.masonryColumnCount;

            if (columnCount <= 1) {{
              return [this.filteredCategories];
            }}

            const columns = Array.from({{ length: columnCount }}, () => ({{ items: [], weight: 0 }}));

            for (const category of this.filteredCategories) {{
              const targetColumn = columns.reduce((lightest, column) => (
                column.weight < lightest.weight ? column : lightest
              ));
              const estimatedHeight = 1 + (category.items.length * 1.2);

              targetColumn.items.push(category);
              targetColumn.weight += estimatedHeight;
            }}

            return columns.map((column) => column.items).filter((column) => column.length > 0);
          }},
          openFirstVisible() {{
            const first = this.filteredCategories[0] && this.filteredCategories[0].items[0];
            if (first) {{
              window.open(first.url, '_blank', 'noopener,noreferrer');
            }}
          }}
        }};
      }}
    </script>
  </body>
</html>
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the dashboard HTML from YAML.")
    parser.add_argument(
        "--source",
        required=True,
        help="Path to the YAML source file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the HTML output file.",
    )
    return parser.parse_args(argv[1:])


def main() -> int:
    args = parse_args(sys.argv)
    source_file = Path(args.source).expanduser().resolve()
    output_file = Path(args.output).expanduser().resolve()
    data = normalize(load_yaml(source_file))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(build_html(data), encoding="utf-8")
    try:
        destination = output_file.relative_to(ROOT)
    except ValueError:
        destination = output_file
    print(f"Wrote {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
