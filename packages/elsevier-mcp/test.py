#!/usr/bin/env python3
"""
Elsevier API 完全テストスイート
=====================

このスクリプトは以下のElsevier APIをテストします：
- Scopus Search API
- Abstract Retrieval API
- ScienceDirect Full-Text API
- SciVal Author Lookup API
- SciVal Author Metrics API

必要な環境変数：
- ELSEVIER_API_KEY: Elsevier APIキー
- ELSEVIER_INSTTOKEN: 機関トークン（ScienceDirectアクセス用）
- TEST_EID: テスト対象論文のEID（任意）
- TEST_AUTHOR_ID: テスト対象著者のScopus ID（任意）
"""

import os
import json
import requests
from typing import Dict, Any, Optional
import sys

class ElsevierAPITester:
    """Elsevier API テストクラス"""

    def __init__(self):
        """初期化"""
        self.api_key = os.getenv('ELSEVIER_API_KEY')
        self.inst_token = os.getenv('ELSEVIER_INSTTOKEN')

        if not self.api_key:
            print("❌ エラー: ELSEVIER_API_KEY環境変数が設定されていません")
            sys.exit(1)

        # テスト用のデフォルト値
        self.test_eid = os.getenv('TEST_EID', '2-s2.0-0035478854')
        self.test_author_id = os.getenv('TEST_AUTHOR_ID', '57215842016')
        self.test_orcid = '0000-0003-1419-2405'

        # APIベースURL
        self.base_urls = {
            'scopus': 'https://api.elsevier.com/content/search/scopus',
            'abstract': 'https://api.elsevier.com/content/abstract',
            'fulltext': 'https://api.elsevier.com/content/article',
            'author_lookup': 'https://api.elsevier.com/content/author',
            'author_metrics': 'https://api.elsevier.com/analytics/scival/author',
            'serial_title': 'https://api.elsevier.com/content/serial/title'
        }

    def get_headers(self, include_inst_token: bool = False) -> Dict[str, str]:
        """APIリクエスト用ヘッダーを生成"""
        headers = {
            'X-ELS-APIKey': self.api_key,
            'Accept': 'application/json'
        }

        if include_inst_token and self.inst_token:
            headers['X-ELS-Insttoken'] = self.inst_token
            print(f"📋 機関トークンを使用: {self.inst_token[:10]}...")

        return headers

    def test_scopus_search(self) -> bool:
        """Scopus Search APIテスト"""
        print("\n🔍 Scopus Search API テスト")
        print("-" * 40)

        try:
            url = self.base_urls['scopus']
            params = {
                'query': 'TITLE-ABS-KEY(robotics)',
                'count': 1,
                'start': 0
            }

            response = requests.get(url, headers=self.get_headers(), params=params)
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                total_results = int(data.get('search-results', {}).get('opensearch:totalResults', 0))
                print(f"✅ 成功: ロボティクス関連論文 {total_results:,} 件見つかりました")

                # 最初の結果を表示
                if data.get('search-results', {}).get('entry'):
                    first_entry = data['search-results']['entry'][0]
                    title = first_entry.get('dc:title', 'タイトル不明')
                    print(f"📄 最新論文例: {title[:100]}...")

                return True
            else:
                print(f"❌ 失敗: HTTP {response.status_code}")
                print(f"エラー内容: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False

    def test_abstract_retrieval(self) -> bool:
        """Abstract Retrieval APIテスト"""
        print("\n📚 Abstract Retrieval API テスト")
        print("-" * 40)

        try:
            url = f"{self.base_urls['abstract']}/eid/{self.test_eid}"

            response = requests.get(url, headers=self.get_headers())
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 論文情報を抽出
                abstract_retrieval = data.get('abstracts-retrieval-response', {})
                core_data = abstract_retrieval.get('coredata', {})

                title = core_data.get('dc:title', 'タイトル不明')
                pub_name = core_data.get('prism:publicationName', '雑誌名不明')
                citation_count = core_data.get('citedby-count', '0')

                print(f"✅ 成功: 論文抄録を取得")
                print(f"📄 タイトル: {title}")
                print(f"📰 雑誌: {pub_name}")
                print(f"📊 被引用数: {citation_count}")

                # 著者情報
                authors = abstract_retrieval.get('authors', {}).get('author', [])
                if authors:
                    author_names = [author.get('ce:indexed-name', 'Unknown') for author in authors[:3]]
                    print(f"👥 著者: {', '.join(author_names)}{'...' if len(authors) > 3 else ''}")

                return True
            else:
                print(f"❌ 失敗: HTTP {response.status_code}")
                print(f"エラー内容: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False

    def test_sciencedirect_fulltext(self) -> bool:
        """ScienceDirect Full-Text APIテスト"""
        print("\n📖 ScienceDirect Full-Text API テスト")
        print("-" * 40)

        try:
            url = f"{self.base_urls['fulltext']}/eid/{self.test_eid}"

            response = requests.get(url, headers=self.get_headers(include_inst_token=True))
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ 成功: 全文データにアクセス可能")

                # レスポンスの構造を確認
                if 'full-text-retrieval-response' in data:
                    print("📋 全文データ構造を確認済み")

                return True
            elif response.status_code == 404:
                print("❌ 404エラー: 全文アクセス不可")
                print("📋 考えられる原因:")
                print("   • 使用中のEIDがElsevier以外の出版社")
                print("   • 機関契約が必要")
                print("   • Institutional Tokenが未設定/無効")

                if not self.inst_token:
                    print("💡 解決方法: ELSEVIER_INSTTOKEN環境変数を設定してください")
                    print("   申請先: apisupport@elsevier.com")

                return False
            else:
                print(f"❌ 失敗: HTTP {response.status_code}")
                print(f"エラー内容: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False

    def test_author_lookup(self) -> bool:
        """SciVal Author Lookup APIテスト"""
        print("\n👤 SciVal Author Lookup API テスト")
        print("-" * 40)

        try:
            url = f"{self.base_urls['author_lookup']}/author_id/{self.test_author_id}"

            response = requests.get(url, headers=self.get_headers())
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 著者情報を抽出
                author_retrieval_response = data.get('author-retrieval-response', [{}])
                if author_retrieval_response:
                    author_profile = author_retrieval_response[0]
                    core_data = author_profile.get('coredata', {})

                    preferred_name = core_data.get('preferred-name') or {}
                    author_name = preferred_name.get('ce:indexed-name', '名前不明')
                    affiliation_current = author_profile.get('affiliation-current') or {}
                    affiliation = affiliation_current.get('affiliation-name', '所属不明')
                    doc_count = core_data.get('document-count', '0')
                    citation_count = core_data.get('cited-by-count', '0')

                    print(f"✅ 成功: 著者情報を取得")
                    print(f"👤 著者名: {author_name}")
                    print(f"🏢 所属: {affiliation}")
                    print(f"📄 論文数: {doc_count}")
                    print(f"📊 被引用数: {citation_count}")

                    return True
                else:
                    print("❌ 著者情報の形式が予期しないものです")
                    return False
            else:
                print(f"❌ 失敗: HTTP {response.status_code}")
                print(f"エラー内容: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False

    def test_author_by_orcid(self) -> bool:
        """ORCID による著者検索テスト"""
        print("\n🆔 ORCID Author Search テスト")
        print("-" * 40)

        try:
            url = f"{self.base_urls['author_lookup']}/orcid/{self.test_orcid}"

            response = requests.get(url, headers=self.get_headers())
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 著者情報を抽出
                author_retrieval_response = data.get('author-retrieval-response', [{}])
                if author_retrieval_response:
                    author_profile = author_retrieval_response[0]
                    core_data = author_profile.get('coredata', {})

                    preferred_name = core_data.get('preferred-name') or {}
                    author_name = preferred_name.get('ce:indexed-name', '名前不明')
                    dc_identifier = core_data.get('dc:identifier') or ''
                    scopus_id = dc_identifier.replace('AUTHOR_ID:', '')

                    print(f"✅ 成功: ORCID検索完了")
                    print(f"🆔 ORCID: {self.test_orcid}")
                    print(f"👤 著者名: {author_name}")
                    print(f"🔢 Scopus ID: {scopus_id}")

                    return True
                else:
                    print("❌ 著者情報の形式が予期しないものです")
                    return False
            else:
                print(f"❌ 失敗: HTTP {response.status_code}")
                print(f"エラー内容: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False

    def test_author_metrics(self) -> bool:
        """SciVal Author Metrics APIテスト"""
        print("\n📈 SciVal Author Metrics API テスト")
        print("-" * 40)

        try:
            url = f"{self.base_urls['author_metrics']}/metrics"
            params = {
                'authors': self.test_author_id,
                'metricTypes': 'CitationCount,ScholarlyOutput',
                'yearRange': '2023-2024',
                'byYear': 'true'
            }

            response = requests.get(url, headers=self.get_headers(), params=params)
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                print("✅ 成功: 著者メトリクスを取得")

                # メトリクスデータを分析
                if 'results' in data and data['results']:
                    author_data = data['results'][0]
                    metrics = author_data.get('metrics', [])

                    for metric in metrics:
                        metric_type = metric.get('metricType', 'Unknown')
                        values = metric.get('valueByYear', [])

                        print(f"\n📊 {metric_type}:")
                        for value_data in values:
                            year = value_data.get('year')
                            value = value_data.get('value', 0)
                            print(f"   {year}年: {value}")

                return True
            else:
                print(f"❌ 失敗: HTTP {response.status_code}")
                print(f"エラー内容: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False

    def test_journal_metrics(self) -> bool:
        """Serial Title / Journal Metrics APIテスト"""
        print("\n📊 Scopus Journal Metrics API テスト")
        print("-" * 40)

        try:
            url = self.base_urls['serial_title']
            params = {
                'title': 'Machine Learning',
                'view': 'CITESCORE',
                'count': 1
            }

            response = requests.get(url, headers=self.get_headers(), params=params)
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                entries = data.get('serial-metadata-response', {}).get('entry', [])
                if entries:
                    entry = entries[0]
                    title = entry.get('dc:title', '不明')
                    citescore = entry.get('citeScoreYearInfoList', {}).get('citeScoreCurrentMetric', 'N/A')
                    print(f"✅ 成功: ジャーナル情報を取得")
                    print(f"📰 タイトル: {title}")
                    print(f"📈 CiteScore: {citescore}")
                    return True
                else:
                    print("❌ 失敗: ジャーナルが見つかりませんでした")
                    return False
            else:
                print(f"❌ 失敗: HTTP {response.status_code}")
                print(f"エラー内容: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False

    def run_all_tests(self):
        """すべてのテストを実行"""
        print("🚀 Elsevier API 完全テストスイート")
        print("=" * 50)
        print(f"📋 APIキー: {self.api_key[:10]}...")
        print(f"📋 機関トークン: {'設定済み' if self.inst_token else '未設定'}")
        print(f"📋 テスト対象EID: {self.test_eid}")
        print(f"📋 テスト対象著者ID: {self.test_author_id}")

        results = {
            'Scopus Search': self.test_scopus_search(),
            'Abstract Retrieval': self.test_abstract_retrieval(),
            'Journal Metrics': self.test_journal_metrics(),
            'ScienceDirect Full-Text': self.test_sciencedirect_fulltext(),
            'Author Lookup': self.test_author_lookup(),
            'ORCID Search': self.test_author_by_orcid(),
            'Author Metrics': self.test_author_metrics()
        }

        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 テスト結果サマリー")
        print("=" * 50)

        success_count = 0
        for test_name, success in results.items():
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"{test_name}: {status}")
            if success:
                success_count += 1

        print(f"\n📈 成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

        if success_count == len(results):
            print("🎉 すべてのAPIが正常に動作しています！")
        elif success_count >= len(results) * 0.8:
            print("🌟 大部分のAPIが動作しています。")
        else:
            print("⚠️  一部のAPIで問題があります。設定を確認してください。")

def main():
    """メイン実行関数"""
    tester = ElsevierAPITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()