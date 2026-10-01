#!/usr/bin/env python3
"""
Elsevier API 完全テストスイート（httpx 版）
=====================

このスクリプトは以下のElsevier APIをテストします：
- Scopus Search API（ページング/ソート、著者別検索、著者候補グルーピング含む）
- Abstract Retrieval API
- ScienceDirect Full-Text API
- SciVal Author Lookup API
- SciVal Author Metrics API

手動のライブチェック用スクリプトです（pytest には含まれません）。
パッケージ本体と同じく httpx を使用します。

必要な環境変数：
- ELSEVIER_API_KEY: Elsevier APIキー
- ELSEVIER_INSTTOKEN: 機関トークン（ScienceDirectアクセス用）
- TEST_EID: テスト対象論文のEID（任意）
- TEST_AUTHOR_ID: テスト対象著者のScopus ID（任意）
- TEST_AUTHOR_NAME: 著者別検索テスト用の著者名（任意、デフォルト "Wahono, R S"）

備考: ScienceDirect全文・Author系エンドポイントは APIキーのエンタイトルメント次第で
403/401 になる（サマリーでは「制限」と表示され、通常の失敗とは区別される）。
"""

import os
import sys
from typing import Any

import httpx


class ElsevierAPITester:
    """Elsevier API テストクラス"""

    def __init__(self) -> None:
        """初期化。APIキーが未設定の場合は None を持ち、run_all_tests() が中断する。"""
        self.api_key: str | None = os.getenv("ELSEVIER_API_KEY")
        self.inst_token: str | None = os.getenv("ELSEVIER_INSTTOKEN")

        # テスト用のデフォルト値
        self.test_eid: str = os.getenv("TEST_EID", "2-s2.0-0035478854")
        self.test_author_id: str = os.getenv("TEST_AUTHOR_ID", "57215842016")
        self.test_orcid: str = "0000-0003-1419-2405"
        self.test_author_name: str = os.getenv("TEST_AUTHOR_NAME", "Wahono, R S")

        # エンタイトルメント制限があるため制限付きキーでは失敗が想定されるテスト
        # （ライブ検証日: 2026-10-01、詳細は .agents/skills/elsevier-mcp-dev/SKILL.md）
        self.known_limited: set[str] = {
            "ScienceDirect Full-Text",
            "Author Lookup",
            "ORCID Search",
            "Author Metrics",
        }

        # APIベースURL
        self.base_urls: dict[str, str] = {
            "scopus": "https://api.elsevier.com/content/search/scopus",
            "abstract": "https://api.elsevier.com/content/abstract",
            "fulltext": "https://api.elsevier.com/content/article",
            "author_lookup": "https://api.elsevier.com/content/author",
            "author_metrics": "https://api.elsevier.com/analytics/scival/author",
            "serial_title": "https://api.elsevier.com/content/serial/title",
        }

    def get_headers(self, include_inst_token: bool = False) -> dict[str, str]:
        """APIリクエスト用ヘッダーを生成

        Args:
            include_inst_token: 機関トークンをヘッダーに含めるか。

        Returns:
            リクエストヘッダー。
        """
        headers = {
            "X-ELS-APIKey": self.api_key or "",
            "Accept": "application/json",
        }

        if include_inst_token and self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token
            print(f"📋 機関トークンを使用: {self.inst_token[:10]}...")

        return headers

    def _print_failure(self, response: httpx.Response) -> None:
        """共通の失敗メッセージを出力する。"""
        print(f"❌ 失敗: HTTP {response.status_code}")
        print(f"エラー内容: {response.text[:200]}")

    def _get(self, url: str, params: dict[str, Any] | None = None, include_inst_token: bool = False) -> httpx.Response:
        """GETリクエストの共通ラッパー。"""
        return httpx.get(
            url,
            headers=self.get_headers(include_inst_token=include_inst_token),
            params=params,
            timeout=30.0,
        )

    def test_scopus_search(self) -> bool:
        """Scopus Search APIテスト"""
        print("\n🔍 Scopus Search API テスト")
        print("-" * 40)

        try:
            response = self._get(
                self.base_urls["scopus"],
                params={"query": "TITLE-ABS-KEY(robotics)", "count": 1, "start": 0},
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                total_results = int(data.get("search-results", {}).get("opensearch:totalResults", 0))
                print(f"✅ 成功: ロボティクス関連論文 {total_results:,} 件見つかりました")

                # 最初の結果を表示
                if data.get("search-results", {}).get("entry"):
                    first_entry = data["search-results"]["entry"][0]
                    title = first_entry.get("dc:title", "タイトル不明")
                    print(f"📄 最新論文例: {title[:100]}...")

                return True

            self._print_failure(response)
            return False

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_abstract_retrieval(self) -> bool:
        """Abstract Retrieval APIテスト"""
        print("\n📚 Abstract Retrieval API テスト")
        print("-" * 40)

        try:
            response = self._get(f"{self.base_urls['abstract']}/eid/{self.test_eid}")
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 論文情報を抽出
                abstract_retrieval = data.get("abstracts-retrieval-response", {})
                core_data = abstract_retrieval.get("coredata", {})

                title = core_data.get("dc:title", "タイトル不明")
                pub_name = core_data.get("prism:publicationName", "雑誌名不明")
                citation_count = core_data.get("citedby-count", "0")

                print("✅ 成功: 論文抄録を取得")
                print(f"📄 タイトル: {title}")
                print(f"📰 雑誌: {pub_name}")
                print(f"📊 被引用数: {citation_count}")

                # 著者情報
                authors = abstract_retrieval.get("authors", {}).get("author", [])
                if authors:
                    author_names = [author.get("ce:indexed-name", "Unknown") for author in authors[:3]]
                    print(f"👥 著者: {', '.join(author_names)}{'...' if len(authors) > 3 else ''}")

                return True

            self._print_failure(response)
            return False

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_sciencedirect_fulltext(self) -> bool:
        """ScienceDirect Full-Text APIテスト"""
        print("\n📖 ScienceDirect Full-Text API テスト")
        print("-" * 40)

        try:
            response = self._get(
                f"{self.base_urls['fulltext']}/eid/{self.test_eid}", include_inst_token=True
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ 成功: 全文データにアクセス可能")

                # レスポンスの構造を確認
                if "full-text-retrieval-response" in data:
                    print("📋 全文データ構造を確認済み")

                return True
            if response.status_code == 404:
                print("❌ 404エラー: 全文アクセス不可")
                print("📋 考えられる原因:")
                print("   • 使用中のEIDがElsevier以外の出版社")
                print("   • 機関契約が必要")
                print("   • Institutional Tokenが未設定/無効")

                if not self.inst_token:
                    print("💡 解決方法: ELSEVIER_INSTTOKEN環境変数を設定してください")
                    print("   申請先: apisupport@elsevier.com")

                return False

            self._print_failure(response)
            return False

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_author_lookup(self) -> bool:
        """SciVal Author Lookup APIテスト"""
        print("\n👤 SciVal Author Lookup API テスト")
        print("-" * 40)

        try:
            response = self._get(f"{self.base_urls['author_lookup']}/author_id/{self.test_author_id}")
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 著者情報を抽出
                author_retrieval_response = data.get("author-retrieval-response", [{}])
                if author_retrieval_response:
                    author_profile = author_retrieval_response[0]
                    core_data = author_profile.get("coredata", {})

                    preferred_name = core_data.get("preferred-name") or {}
                    author_name = preferred_name.get("ce:indexed-name", "名前不明")
                    affiliation_current = author_profile.get("affiliation-current") or {}
                    affiliation = affiliation_current.get("affiliation-name", "所属不明")
                    doc_count = core_data.get("document-count", "0")
                    citation_count = core_data.get("cited-by-count", "0")

                    print("✅ 成功: 著者情報を取得")
                    print(f"👤 著者名: {author_name}")
                    print(f"🏢 所属: {affiliation}")
                    print(f"📄 論文数: {doc_count}")
                    print(f"📊 被引用数: {citation_count}")

                    return True

                print("❌ 著者情報の形式が予期しないものです")
                return False

            self._print_failure(response)
            return False

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_author_by_orcid(self) -> bool:
        """ORCID による著者検索テスト"""
        print("\n🆔 ORCID Author Search テスト")
        print("-" * 40)

        try:
            response = self._get(f"{self.base_urls['author_lookup']}/orcid/{self.test_orcid}")
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 著者情報を抽出
                author_retrieval_response = data.get("author-retrieval-response", [{}])
                if author_retrieval_response:
                    author_profile = author_retrieval_response[0]
                    core_data = author_profile.get("coredata", {})

                    preferred_name = core_data.get("preferred-name") or {}
                    author_name = preferred_name.get("ce:indexed-name", "名前不明")
                    dc_identifier = core_data.get("dc:identifier") or ""
                    scopus_id = dc_identifier.replace("AUTHOR_ID:", "")

                    print("✅ 成功: ORCID検索完了")
                    print(f"🆔 ORCID: {self.test_orcid}")
                    print(f"👤 著者名: {author_name}")
                    print(f"🔢 Scopus ID: {scopus_id}")

                    return True

                print("❌ 著者情報の形式が予期しないものです")
                return False

            self._print_failure(response)
            return False

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_author_metrics(self) -> bool:
        """SciVal Author Metrics APIテスト"""
        print("\n📈 SciVal Author Metrics API テスト")
        print("-" * 40)

        try:
            response = self._get(
                f"{self.base_urls['author_metrics']}/metrics",
                params={
                    "authors": self.test_author_id,
                    "metricTypes": "CitationCount,ScholarlyOutput",
                    "yearRange": "2023-2024",
                    "byYear": "true",
                },
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                print("✅ 成功: 著者メトリクスを取得")

                # メトリクスデータを分析
                if data.get("results"):
                    author_data = data["results"][0]
                    metrics = author_data.get("metrics", [])

                    for metric in metrics:
                        metric_type = metric.get("metricType", "Unknown")
                        values = metric.get("valueByYear", [])

                        print(f"\n📊 {metric_type}:")
                        for value_data in values:
                            year = value_data.get("year")
                            value = value_data.get("value", 0)
                            print(f"   {year}年: {value}")

                return True

            self._print_failure(response)
            return False

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_journal_metrics(self) -> bool:
        """Serial Title / Journal Metrics APIテスト"""
        print("\n📊 Scopus Journal Metrics API テスト")
        print("-" * 40)

        try:
            response = self._get(
                self.base_urls["serial_title"],
                params={"title": "Machine Learning", "view": "CITESCORE", "count": 1},
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                entries = data.get("serial-metadata-response", {}).get("entry", [])
                if entries:
                    entry = entries[0]
                    title = entry.get("dc:title", "不明")
                    citescore = entry.get("citeScoreYearInfoList", {}).get("citeScoreCurrentMetric", "N/A")
                    print("✅ 成功: ジャーナル情報を取得")
                    print(f"📰 タイトル: {title}")
                    print(f"📈 CiteScore: {citescore}")
                    return True

                print("❌ 失敗: ジャーナルが見つかりませんでした")
                return False

            self._print_failure(response)
            return False

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_search_pagination(self) -> bool:
        """Scopus Search ページング/ソートテスト（start/sort パラメータ）"""
        print("\n📄 Scopus Search Pagination テスト")
        print("-" * 40)

        try:
            page1 = self._get(
                self.base_urls["scopus"],
                params={
                    "query": "TITLE-ABS-KEY(machine learning)",
                    "count": 5,
                    "start": 0,
                    "sort": "citedby-count",
                },
            )
            print(f"URL: {page1.url}")
            print(f"Status: {page1.status_code}")

            if page1.status_code != 200:
                self._print_failure(page1)
                return False

            results1 = page1.json().get("search-results", {})
            entries1 = results1.get("entry", []) or []
            total = int(results1.get("opensearch:totalResults", 0))
            print(f"✅ 成功: 総件数 {total:,} 件、1ページ目 {len(entries1)} 件取得")

            citations = [int(e.get("citedby-count", 0)) for e in entries1]
            if citations != sorted(citations, reverse=True):
                print("❌ 失敗: citedby-count ソートが降順になっていません")
                return False

            page2 = self._get(
                self.base_urls["scopus"],
                params={
                    "query": "TITLE-ABS-KEY(machine learning)",
                    "count": 5,
                    "start": 5,
                    "sort": "citedby-count",
                },
            )
            if page2.status_code != 200:
                self._print_failure(page2)
                return False

            results2 = page2.json().get("search-results", {})
            entries2 = results2.get("entry", []) or []
            start_index = results2.get("opensearch:startIndex")
            print(f"📄 2ページ目: start={start_index}, {len(entries2)} 件")

            title1 = entries1[0].get("dc:title", "") if entries1 else ""
            title2 = entries2[0].get("dc:title", "") if entries2 else ""
            if str(start_index) != "5" or title1 == title2:
                print("❌ 失敗: 2ページ目が正しくシフトしていません")
                return False

            print(f"📄 1ページ目先頭: {title1[:80]}...")
            print(f"📄 2ページ目先頭: {title2[:80]}...")
            return True

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_author_papers_search(self) -> bool:
        """AUTH(\"...\") 著者別論文検索テスト（search_author_papers 相当）"""
        print("\n👥 Author Papers Search テスト")
        print("-" * 40)

        try:
            response = self._get(
                self.base_urls["scopus"],
                params={
                    "query": f'AUTH("{self.test_author_name}")',
                    "count": 3,
                    "sort": "citedby-count",
                },
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code != 200:
                self._print_failure(response)
                return False

            data = response.json()
            results = data.get("search-results", {})
            total = int(results.get("opensearch:totalResults", 0))
            entries = results.get("entry", []) or []
            print(f"✅ 成功: AUTH(\"{self.test_author_name}\") → 総件数 {total:,} 件")
            for entry in entries[:3]:
                title = entry.get("dc:title", "タイトル不明")
                creator = entry.get("dc:creator", "著者不明")
                print(f"   📄 {title[:70]}... (筆頭著者: {creator})")

            print("⚠️  注意: イニシャル名義はホモニム混入リスクあり — find_author_candidates で確認を推奨")
            return True

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def test_find_author_candidates(self) -> bool:
        """著者候補グルーピングテスト（find_author_candidates 相当）"""
        print("\n🔍 Author Candidates Grouping テスト")
        print("-" * 40)

        try:
            response = self._get(
                self.base_urls["scopus"],
                params={
                    "query": f'AUTH("{self.test_author_name}")',
                    "count": 10,
                    "sort": "citedby-count",
                    "field": "dc:creator,authid,affilname,prism:coverDate",
                },
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code != 200:
                self._print_failure(response)
                return False

            data = response.json()
            entries = data.get("search-results", {}).get("entry", []) or []

            # クライアント側でグルーピング（MCP find_author_candidates と同じ発想）
            grouped: dict[str, int] = {}
            authids: set[str] = set()
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                creator = entry.get("dc:creator", "Unknown")
                affils = entry.get("affiliation") or []
                affil_names = [
                    str(a.get("affilname", "")) for a in (affils if isinstance(affils, list) else [affils]) if isinstance(a, dict)
                ]
                key = f"{creator} @ {', '.join(n for n in affil_names if n) or '所属不明'}"
                grouped[key] = grouped.get(key, 0) + 1
                raw_authid = entry.get("authid")
                if isinstance(raw_authid, list):
                    authids.update(str(x) for x in raw_authid if x)
                elif raw_authid:
                    authids.add(str(raw_authid))

            print(f"✅ 成功: {len(entries)} 件のサンプルから {len(grouped)} 候補にグループ化")
            for key, count in sorted(grouped.items(), key=lambda kv: kv[1], reverse=True)[:5]:
                print(f"   👤 {key} ({count} 件)")
            if authids:
                print(f"🆔 取得できた著者ID: {', '.join(sorted(authids))}")
            else:
                print("🆔 著者IDは返却されませんでした（制限付きキーの通常挙動、名前＋所属でグループ化）")
            print("⚠️  注意: 複数候補が出た場合、同姓同名（ホモニム）混入の可能性あり")
            return True

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False

    def run_all_tests(self) -> int:
        """すべてのテストを実行し、成功数を返す。

        Returns:
            成功したテストの数。
        """
        print("🚀 Elsevier API 完全テストスイート")
        print("=" * 50)
        if not self.api_key:
            print("❌ エラー: ELSEVIER_API_KEY環境変数が設定されていません")
            return 0

        masked_key = self.api_key[:10]
        print(f"📋 APIキー: {masked_key}...")
        print(f"📋 機関トークン: {'設定済み' if self.inst_token else '未設定'}")
        print(f"📋 テスト対象EID: {self.test_eid}")
        print(f"📋 テスト対象著者ID: {self.test_author_id}")

        results = {
            "Scopus Search": self.test_scopus_search(),
            "Scopus Pagination": self.test_search_pagination(),
            "Author Papers Search": self.test_author_papers_search(),
            "Author Candidates Grouping": self.test_find_author_candidates(),
            "Abstract Retrieval": self.test_abstract_retrieval(),
            "Journal Metrics": self.test_journal_metrics(),
            "ScienceDirect Full-Text": self.test_sciencedirect_fulltext(),
            "Author Lookup": self.test_author_lookup(),
            "ORCID Search": self.test_author_by_orcid(),
            "Author Metrics": self.test_author_metrics(),
        }

        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 テスト結果サマリー")
        print("=" * 50)

        success_count = 0
        limited_failure_count = 0
        for test_name, success in results.items():
            if success:
                print(f"{test_name}: ✅ 成功")
                success_count += 1
            elif test_name in self.known_limited:
                print(f"{test_name}: ⚠️  制限（エンタイトルメントなし、想定内）")
                limited_failure_count += 1
            else:
                print(f"{test_name}: ❌ 失敗")

        print(
            f"\n📈 成功率: {success_count}/{len(results)} "
            f"({success_count / len(results) * 100:.1f}%)、"
            f"内 {limited_failure_count} 件はエンタイトルメント制限"
        )

        unexpected_failures = len(results) - success_count - limited_failure_count
        if unexpected_failures == 0:
            print("🎉 全ての利用可能なAPIが正常に動作しています！")
        else:
            print("⚠️  想定外の失敗があります。設定を確認してください。")

        return success_count


def main() -> None:
    """メイン実行関数"""
    tester = ElsevierAPITester()
    count = tester.run_all_tests()
    if count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
