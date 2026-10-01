---
description: Hasil pengujian komprehensif rilis v1.3.0 Elsevier_MCP — matriks unit/integrasi/e2e/live, coverage, smoke test wheel, dan temuan entitlemen API.
tags:
  - pengujian
  - quality-assurance
  - v1-3-0
  - scopus
  - integration-testing
  - research
title: Laporan Pengujian Komprehensif v1.3.0 — Elsevier MCP Server
---

# Laporan Pengujian Komprehensif v1.3.0 — Elsevier MCP Server

## Ringkasan Eksekutif

Pengujian komprehensif untuk rilis **v1.3.0** (commit `2848bf0`) dilaksanakan pada **2026-10-01** mencakup lima lapisan: test skema/validasi, unit test handler, test REST API, smoke test paket wheel di venv terpisah, dan live test API Elsevier dengan key asli. **Seluruh 146 test otomatis lulus** (102 core + 30 API + 7 web unit + 7 e2e Playwright), coverage Python naik ke **93,5%** (core) dan **92%** (API), wheel 1.3.0 terverifikasi terpasang bersih di venv segar (termasuk Python 3.14), dan live test mengkonfirmasi 6/10 endpoint bekerja dengan 4 lainnya terbatas entitlemen (bukan bug).

Pengujian ini juga **menemukan dan memperbaiki satu bug riil**: field `sort` belum dideklarasikan pada `AuthorPapersBody` di `apps/api/app/routers/papers.py` sehingga parameter sort dari klien terdiam dibuang (tertangkap oleh test clamp/passthrough).

## Matriks Hasil

| Lapisan | Skop | Hasil | Catatan |
|---|---|---|---|
| Skema (pytest) | Validasi Pydantic 9 model input | ✅ lulus | Default/batas `start` 0–5999, set `sort`, keharusan `author_id`/`author_name`, format tahun |
| Unit handler (pytest) | 9 tool MCP + helper pengelompokan | ✅ **102 lulus** | Coverage **93,5%** (naik dari 92,9%) |
| Regression lock | Bentuk response lintas tool | ✅ lulus | Kunci shape `search_papers` kini termasuk `start` |
| REST API (pytest) | 10 route FastAPI via TestClient | ✅ **30 lulus** | Coverage **92%**; test clamp `start`→5999, `count`→25, passthrough `year`/`sort` |
| Web unit (node:test) | `api-client.ts` (`fmt`, heuristik ISSN) | ✅ 7 lulus | — |
| e2e Playwright | 5 halaman + navigasi (Chromium) | ✅ 7 lulus | Termasuk tab Institutions baru |
| Smoke wheel | venv segar, `pip install` wheel 1.3.0 | ✅ lulus | `--version` → 1.3.0; stdio `tools/list` → 9 tool; **Python 3.14** kompatibel meski classifier hanya 3.10–3.12 |
| Live API (test.py) | 10 endpoint dengan key asli | ✅ 6/10 | 4 sisanya terbatas entitlemen — terlabeli "制限", bukan gagal |

## Yang Ditambahkan dalam Pengujian Ini

1. **Test skema baru** (`tests/test_schemas.py`): paginasi `search_papers` (default 0, batas atas 5999, penolakan `sort` di luar set), `SearchAuthorPapersInput` (wajib salah satu dari `author_id`/`author_name`, strip whitespace, validasi tahun/sort/batas), `FindAuthorCandidatesInput` (strip, batas `count` 1–25).
2. **Test unit helper pengelompokan** (`tests/test_handlers.py`): `group_author_candidates` terhadap entri kosong/malformed, varian bentuk `authid` (string/int/list), bentuk dict `affiliation`, pelacakan `latest_year`, dan urutan berdasarkan jumlah dokumen.
3. **Test REST API** (`apps/api/tests/test_endpoints.py`): `/api/author-papers` dengan parameter lengkap (clamp `count` 100→25, `start` 9999→5999, passthrough `year` sebagai string dan `sort`).
4. **test.py live diperluas**: tiga test baru — paginasi Scopus (verifikasi urutan `citedby-count` menurun + pergeseran `startIndex` antar halaman), penelusuran penulis `AUTH("nama")`, dan pengelompokan kandidat penulis dengan seleksi field. Endpoint terbatas entitlemen kini dilabeli eksplisit di ringkasan sehingga keberhasilan live tidak lagi menipu.

## Temuan Live API (key repo, 2026-10-01)

| Endpoint | Status | Implikasi |
|---|---|---|
| `content/search/scopus` (termasuk `start`/`sort`/`AUTH`) | ✅ 200 | Jalur utama semua fitur baru |
| `content/abstract/eid/{eid}` | ✅ 200 | — |
| `content/serial/title` (CiteScore) | ✅ 200 | — |
| `content/abstract/citations/{eid}` | ❌ 403 | Tidak dibuatkan tool |
| `content/article/...` (ScienceDirect full text) | ❌ 403 | Tidak dibuatkan tool |
| `content/author/...` + ORCID | ❌ 401 | `AUTH("nama")` + filter afiliasi satu-satunya jalur penulis |
| `analytics/scival/author/...` | ❌ 403 | Tool `get_author_info` selalu error dict dengan key ini |
| `field=authid` di general search | ⚠️ 200 tapi ID tak dikembalikan | `find_author_candidates` terdegradasi mulus ke pengelompokan nama+afiliasi |

Detail lengkap batasan entitlemen terdokumentasi di `.agents/skills/elsevier-mcp-dev/SKILL.md` §"Known API-key entitlement limits".

## Bug yang Ditemukan & Diperbaiki

- **`AuthorPapersBody.sort` tidak ada** (ditemukan test passthrough): request `sort` dari klien diabaikan diam-diam oleh Pydantic. Diperbaiki dengan menambahkan field dan meneruskannya ke handler (`37fd71d`).

## Catatan & Batasan Pengujian

- Live test bersifat *read-only* (GET) dan membutuhkan `ELSEVIER_API_KEY` (`set -a; source .env`).
- Sisi frontend sengaja hanya diuji unit minim + e2e smoke, sesuai keputusan QA minimal yang disepakati; tidak ada pengujian browser interaktif terhadap backend hidup dalam laporan ini (integration web↔api divalidasi lewat kontrak MockToolHandlers dan konfigurasi BFF).
- Workflow Actions repo ini tidak terpicu oleh push (teredam di level akun — diduga verifikasi email); rilis v1.3.0 dibuat via dispatch manual `gh workflow run Release --ref v1.3.0`.
