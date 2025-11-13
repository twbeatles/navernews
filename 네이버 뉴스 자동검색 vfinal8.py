# --- 필요 라이브러리 설치 안내 ---
# pip install PyQt6 requests
import sys
import json
import traceback
import requests
import os
import html
import urllib.parse
import sqlite3
import threading
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextBrowser, QLabel, QMessageBox,
    QTabWidget, QInputDialog, QComboBox, QFileDialog, QSystemTrayIcon,
    QMenu, QStyle, QTabBar, QDialog, QDialogButtonBox, QGroupBox,
    QGridLayout, QProgressBar
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, Qt, QTimer, QUrl, QByteArray, QMutex
from PyQt6.QtGui import QDesktopServices, QIcon, QAction

# --- 상수 정의 ---
CONFIG_FILE = "news_scraper_config.json"
DB_FILE = "news_database.db"
VERSION = "18.2"  # 디버깅 버전

# --- 라이트 테마 스타일시트 ---
LIGHT_STYLESHEET = """
    QMainWindow, QDialog { background-color: #F0F2F5; }
    QGroupBox { font-family: '맑은 고딕'; }
    QLabel, QDialog QLabel { font-family: '맑은 고딕'; font-size: 10pt; color: #000000; }
    QPushButton { font-family: '맑은 고딕'; font-size: 10pt; background-color: #FFFFFF; color: #333; padding: 8px 12px; border-radius: 6px; border: 1px solid #DCDCDC; }
    QPushButton:hover { background-color: #E8E8E8; }
    QPushButton:disabled { background-color: #F5F5F5; color: #999; }
    QPushButton#AddTab { font-weight: bold; background-color: #007AFF; color: white; border: none; }
    QPushButton#AddTab:hover { background-color: #0056b3; }
    QComboBox { font-family: '맑은 고딕'; font-size: 10pt; padding: 5px; border-radius: 6px; border: 1px solid #ccc; background-color: #FFFFFF; color: #000000; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { font-family: '맑은 고딕'; font-size: 10pt; background-color: #FFFFFF; color: #000000; border: 1px solid #DCDCDC; selection-background-color: #007AFF; selection-color: #FFFFFF; outline: 0px; }
    QTextBrowser { font-family: '맑은 고딕'; background-color: #FFFFFF; border: 1px solid #DCDCDC; border-radius: 8px; }
    QTabWidget::pane { border-top: 1px solid #DCDCDC; }
    QTabBar::tab { font-family: '맑은 고딕'; font-size: 10pt; color: #333; padding: 10px 15px; border: 1px solid transparent; border-bottom: none; background-color: transparent; }
    QTabBar::tab:selected { background-color: #FFFFFF; border-color: #DCDCDC; border-top-left-radius: 6px; border-top-right-radius: 6px; color: #000; font-weight: bold; }
    QTabBar::tab:!selected { color: #777; }
    QTabBar::tab:!selected:hover { color: #333; }
    QLineEdit { font-family: '맑은 고딕'; font-size: 10pt; padding: 5px 8px; border-radius: 6px; border: 1px solid #ccc; background-color: #FFFFFF; color: #000000; }
    QLineEdit#FilterActive { border: 2px solid #007AFF; background-color: #F0F8FF; }
    QProgressBar { border: 1px solid #DCDCDC; border-radius: 3px; text-align: center; background-color: #FFFFFF; }
    QProgressBar::chunk { background-color: #007AFF; }
"""

# --- 다크 테마 스타일시트 ---
DARK_STYLESHEET = """
    QMainWindow, QDialog { background-color: #2E2E2E; }
    QGroupBox { font-family: '맑은 고딕'; color: #E0E0E0; }
    QLabel, QDialog QLabel { font-family: '맑은 고딕'; font-size: 10pt; color: #E0E0E0; }
    QPushButton { font-family: '맑은 고딕'; font-size: 10pt; background-color: #4A4A4A; color: #E0E0E0; padding: 8px 12px; border-radius: 6px; border: 1px solid #606060; }
    QPushButton:hover { background-color: #5A5A5A; }
    QPushButton:disabled { background-color: #3A3A3A; color: #666; }
    QPushButton#AddTab { font-weight: bold; background-color: #0A84FF; color: white; border: none; }
    QPushButton#AddTab:hover { background-color: #0060C0; }
    QComboBox { font-family: '맑은 고딕'; font-size: 10pt; padding: 5px; border-radius: 6px; border: 1px solid #606060; background-color: #4A4A4A; color: #E0E0E0; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { font-family: '맑은 고딕'; font-size: 10pt; background-color: #4A4A4A; color: #E0E0E0; border: 1px solid #606060; selection-background-color: #0A84FF; selection-color: #FFFFFF; outline: 0px; }
    QTextBrowser { font-family: '맑은 고딕'; background-color: #3C3C3C; border: 1px solid #606060; border-radius: 8px; color: #E0E0E0; }
    QTabWidget::pane { border-top: 1px solid #606060; }
    QTabBar::tab { font-family: '맑은 고딕'; font-size: 10pt; color: #CCCCCC; padding: 10px 15px; border: 1px solid transparent; border-bottom: none; background-color: transparent; }
    QTabBar::tab:selected { background-color: #3C3C3C; border-color: #606060; border-top-left-radius: 6px; border-top-right-radius: 6px; color: #FFFFFF; font-weight: bold; }
    QTabBar::tab:!selected { color: #AAAAAA; }
    QTabBar::tab:!selected:hover { color: #FFFFFF; }
    QLineEdit { font-family: '맑은 고딕'; font-size: 10pt; padding: 5px 8px; border-radius: 6px; border: 1px solid #606060; background-color: #4A4A4A; color: #E0E0E0; }
    QLineEdit#FilterActive { border: 2px solid #0A84FF; background-color: #2A3A4A; }
    QProgressBar { border: 1px solid #606060; border-radius: 3px; text-align: center; background-color: #3C3C3C; color: #E0E0E0; }
    QProgressBar::chunk { background-color: #0A84FF; }
"""

# --- 스레드 안전 데이터베이스 관리 클래스 ---
class DatabaseManager:
    """스레드 안전 SQLite 데이터베이스 연결 및 쿼리를 관리합니다."""
    def __init__(self, db_file):
        self.db_file = db_file
        self.local = threading.local()
        self.mutex = QMutex()
        self._init_db()

    def _get_conn(self):
        """스레드별 데이터베이스 연결을 반환합니다."""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_file, timeout=30.0)
            self.local.conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging 활성화
        return self.local.conn

    def _init_db(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_file, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            self.create_tables(conn)
            self._check_and_migrate_db(conn)
        finally:
            conn.close()

    def _check_and_migrate_db(self, conn):
        """기존 DB 스키마를 확인하고 정렬을 위한 타임스탬프 컬럼을 추가합니다."""
        try:
            cursor = conn.execute("PRAGMA table_info(news)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'pubDate_ts' not in columns:
                with conn:
                    conn.execute("ALTER TABLE news ADD COLUMN pubDate_ts REAL")
            if 'created_at' not in columns:
                with conn:
                    conn.execute("ALTER TABLE news ADD COLUMN created_at REAL DEFAULT 0")
        except sqlite3.Error as e:
            print(f"DB 마이그레이션 오류: {e}")

    def create_tables(self, conn):
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    link TEXT PRIMARY KEY,
                    keyword TEXT,
                    title TEXT,
                    description TEXT,
                    pubDate TEXT,
                    publisher TEXT,
                    is_read INTEGER DEFAULT 0,
                    is_bookmarked INTEGER DEFAULT 0,
                    data TEXT,
                    pubDate_ts REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON news(keyword)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bookmarked ON news(is_bookmarked)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pubdate ON news(pubDate_ts)")
    
    def add_news_items(self, keyword, news_items):
        """새 뉴스 아이템을 추가하고 추가된 개수를 반환합니다."""
        added_count = 0
        conn = self._get_conn()
        
        try:
            self.mutex.lock()
            with conn:
                for item in news_items:
                    pub_timestamp = 0.0
                    try:
                        pub_timestamp = parsedate_to_datetime(item['pubDate']).timestamp()
                    except Exception:
                        pass

                    try:
                        cursor = conn.execute("""
                            INSERT OR IGNORE INTO news (link, keyword, title, description, pubDate, publisher, data, pubDate_ts)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (item['link'], keyword, item['title'], item['description'], 
                              item['pubDate'], item['publisher'], json.dumps(item), pub_timestamp))
                        
                        if cursor.rowcount > 0:
                            added_count += 1
                    except sqlite3.IntegrityError:
                        continue  # 이미 존재하는 항목
        except Exception as e:
            print(f"DB 추가 오류: {e}")
        finally:
            self.mutex.unlock()
        
        return added_count

    def get_news(self, keyword, filter_text, sort_order, limit=None):
        conn = self._get_conn()
        query = "SELECT data, is_read, is_bookmarked FROM news WHERE keyword = ?"
        params = [keyword]
        if filter_text:
            query += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{filter_text}%", f"%{filter_text}%"])
        
        order = "DESC" if sort_order == "최신순" else "ASC"
        query += f" ORDER BY pubDate_ts {order}"
        
        if limit:
            query += f" LIMIT {limit}"

        try:
            cursor = conn.execute(query, tuple(params))
            return [
                {**json.loads(row[0]), 'is_read': bool(row[1]), 'is_bookmarked': bool(row[2])}
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"DB 조회 오류: {e}")
            return []

    def get_news_count(self, keyword):
        """특정 키워드의 뉴스 개수를 반환합니다."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM news WHERE keyword = ?", (keyword,))
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"DB 카운트 오류: {e}")
            return 0

    def get_unread_count(self, keyword):
        """읽지 않은 뉴스 개수를 반환합니다."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM news WHERE keyword = ? AND is_read = 0", (keyword,))
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"DB 미독 카운트 오류: {e}")
            return 0

    def get_bookmarks(self, filter_text, sort_order):
        conn = self._get_conn()
        query = "SELECT data, is_read FROM news WHERE is_bookmarked = 1"
        params = []
        if filter_text:
            query += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{filter_text}%", f"%{filter_text}%"])
        
        order = "DESC" if sort_order == "최신순" else "ASC"
        query += f" ORDER BY pubDate_ts {order}"

        try:
            cursor = conn.execute(query, tuple(params))
            return [
                {**json.loads(row[0]), 'is_read': bool(row[1]), 'is_bookmarked': True}
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"DB 북마크 조회 오류: {e}")
            return []

    def set_read_status(self, link, is_read):
        conn = self._get_conn()
        try:
            self.mutex.lock()
            with conn:
                conn.execute("UPDATE news SET is_read = ? WHERE link = ?", (int(is_read), link))
        except Exception as e:
            print(f"DB 읽음 상태 변경 오류: {e}")
        finally:
            self.mutex.unlock()

    def mark_all_as_read(self, keyword):
        conn = self._get_conn()
        try:
            self.mutex.lock()
            with conn:
                if keyword == "북마크":
                    conn.execute("UPDATE news SET is_read = 1 WHERE is_bookmarked = 1")
                else:
                    conn.execute("UPDATE news SET is_read = 1 WHERE keyword = ?", (keyword,))
        except Exception as e:
            print(f"DB 전체 읽음 처리 오류: {e}")
        finally:
            self.mutex.unlock()

    def toggle_bookmark(self, link):
        conn = self._get_conn()
        try:
            self.mutex.lock()
            with conn:
                cursor = conn.execute("SELECT is_bookmarked FROM news WHERE link = ?", (link,))
                result = cursor.fetchone()
                if result:
                    current_status = result[0]
                    conn.execute("UPDATE news SET is_bookmarked = ? WHERE link = ?", (1 - current_status, link))
        except Exception as e:
            print(f"DB 북마크 토글 오류: {e}")
        finally:
            self.mutex.unlock()

    def prune_old_news(self, days=30):
        """북마크되지 않은 오래된 뉴스를 삭제합니다."""
        conn = self._get_conn()
        try:
            cutoff_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
            self.mutex.lock()
            with conn:
                cursor = conn.execute(
                    "DELETE FROM news WHERE is_bookmarked = 0 AND pubDate_ts < ?",
                    (cutoff_timestamp,)
                )
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"오래된 뉴스 삭제 오류: {e}")
            return -1
        finally:
            self.mutex.unlock()

    def clear_all_news(self):
        """북마크되지 않은 모든 뉴스를 삭제합니다."""
        conn = self._get_conn()
        try:
            self.mutex.lock()
            with conn:
                cursor = conn.execute("DELETE FROM news WHERE is_bookmarked = 0")
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"모든 뉴스 삭제 오류: {e}")
            return -1
        finally:
            self.mutex.unlock()

    def close(self):
        """모든 스레드의 연결을 정리합니다."""
        if hasattr(self.local, 'conn') and self.local.conn:
            try:
                self.local.conn.close()
            except:
                pass

# --- 설정 다이얼로그 ---
class SettingsDialog(QDialog):
    """API 키, 자동 새로고침, 테마 등 다양한 설정을 관리하기 위한 대화창 클래스입니다."""
    def __init__(self, parent=None, config=None, db=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        self.config = config if config else {}
        self.db = db
        
        layout = QVBoxLayout(self)
        
        # API 설정 그룹
        api_group = QGroupBox("네이버 API 설정")
        api_layout = QVBoxLayout(api_group)
        info_label = QLabel("<a href='https://developers.naver.com/apps'>네이버 개발자 센터에서 발급</a>받은 Client ID와 Secret을 입력하세요.")
        info_label.setOpenExternalLinks(True)
        api_layout.addWidget(info_label)
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Client ID:"))
        self.id_input = QLineEdit(self.config.get("client_id", ""))
        id_layout.addWidget(self.id_input)
        api_layout.addLayout(id_layout)
        secret_layout = QHBoxLayout()
        secret_layout.addWidget(QLabel("Client Secret:"))
        self.secret_input = QLineEdit(self.config.get("client_secret", ""))
        self.secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        secret_layout.addWidget(self.secret_input)
        api_layout.addLayout(secret_layout)
        layout.addWidget(api_group)

        # 일반 설정 그룹
        general_group = QGroupBox("일반 설정")
        general_layout = QGridLayout(general_group)
        general_layout.addWidget(QLabel("새로고침 간격:"), 0, 0)
        self.refresh_combo = QComboBox()
        self.refresh_combo.addItems(["10분", "30분", "1시간", "3시간", "6시간", "자동 새로고침 안함"])
        self.refresh_combo.setCurrentIndex(self.config.get("refresh_interval_index", 2))
        general_layout.addWidget(self.refresh_combo, 0, 1)

        general_layout.addWidget(QLabel("앱 테마:"), 1, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["라이트 모드", "다크 모드"])
        self.theme_combo.setCurrentIndex(self.config.get("theme_index", 0))
        general_layout.addWidget(self.theme_combo, 1, 1)
        layout.addWidget(general_group)
        
        # 데이터 관리 그룹
        data_group = QGroupBox("데이터 관리")
        data_layout = QVBoxLayout(data_group)
        data_layout.addWidget(QLabel("데이터베이스에 저장된 기사를 관리합니다."))
        
        self.prune_button = QPushButton("오래된 기사 삭제 (발행일 30일 경과, 북마크 제외)")
        self.prune_button.clicked.connect(self.prune_data)
        data_layout.addWidget(self.prune_button)
        
        self.clear_button = QPushButton("모든 기사 삭제 (북마크 제외)")
        self.clear_button.clicked.connect(self.clear_data)
        data_layout.addWidget(self.clear_button)
        
        layout.addWidget(data_group)
        layout.addStretch(1)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def prune_data(self):
        """오래된 기사 삭제 버튼 클릭 시"""
        if not self.db: return
        
        reply = QMessageBox.question(self, "확인", 
                                     "북마크되지 않고 발행일로부터 30일이 지난 모든 기사를 DB에서 삭제하시겠습니까?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Cancel)
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = self.db.prune_old_news(days=30)
            if deleted_count >= 0:
                QMessageBox.information(self, "완료", f"{deleted_count}개의 오래된 기사를 삭제했습니다.")
                self.parent().redraw_all_tabs()
            else:
                QMessageBox.warning(self, "오류", "데이터 삭제 중 오류가 발생했습니다.")

    def clear_data(self):
        """모든 기사 삭제 버튼 클릭 시"""
        if not self.db: return

        reply = QMessageBox.question(self, "경고", 
                                     "정말로 북마크되지 않은 *모든* 기사를 DB에서 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Cancel)
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = self.db.clear_all_news()
            if deleted_count >= 0:
                QMessageBox.information(self, "완료", f"{deleted_count}개의 기사를 삭제했습니다.")
                self.parent().redraw_all_tabs()
            else:
                QMessageBox.warning(self, "오류", "데이터 삭제 중 오류가 발생했습니다.")

    def get_settings(self):
        return {
            "client_id": self.id_input.text().strip(),
            "client_secret": self.secret_input.text().strip(),
            "refresh_interval_index": self.refresh_combo.currentIndex(),
            "theme_index": self.theme_combo.currentIndex()
        }

# --- 백그라운드 API 요청을 위한 Worker 클래스 ---
class Worker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, keyword, exclude_keywords, client_id, client_secret, start=1):
        super().__init__()
        self.keyword = keyword
        self.exclude_keywords = exclude_keywords
        self.start = start
        self.client_id = client_id
        self.client_secret = client_secret
        self._is_cancelled = False

    def cancel(self):
        """작업 취소 플래그 설정"""
        self._is_cancelled = True

    @pyqtSlot()
    def run(self):
        if self._is_cancelled:
            return
            
        session = None
        try:
            # 각 요청마다 새로운 세션 생성 (연결 풀 문제 방지)
            session = requests.Session()
            session.headers.update({
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
            })
            
            result_dict = self.fetch_naver_news(session)
            
            if not self._is_cancelled:
                self.finished.emit(result_dict)
                
        except requests.exceptions.Timeout:
            if not self._is_cancelled:
                self.error.emit("요청 시간이 초과되었습니다. 네트워크 상태를 확인해주세요.")
        except requests.exceptions.ConnectionError:
            if not self._is_cancelled:
                self.error.emit("인터넷 연결을 확인해주세요.")
        except requests.exceptions.RequestException as e:
            if not self._is_cancelled:
                self.error.emit(f"네트워크 오류가 발생했습니다.\n잠시 후 다시 시도해주세요.")
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"예기치 않은 오류가 발생했습니다: {str(e)}")
        finally:
            if session:
                try:
                    session.close()
                except:
                    pass

    def fetch_naver_news(self, session):
        if self._is_cancelled:
            return {'items': [], 'total': 0}
            
        api_url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": self.keyword, "display": 100, "sort": "date", "start": self.start}
        
        response = session.get(api_url, params=params, timeout=15)

        if response.status_code == 401:
            raise Exception("API 인증에 실패했습니다. 설정에서 API 키를 확인해주세요.")
        elif response.status_code == 429:
            raise Exception("API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
        elif response.status_code != 200:
            raise Exception(f"API 오류 (코드: {response.status_code})")

        response_json = response.json()
        total_results = response_json.get("total", 0)
        processed_news = []

        for item in response_json.get("items", []):
            if self._is_cancelled:
                break
                
            title = html.unescape(item.get('title', '')).replace('<b>', '').replace('</b>', '')
            description = html.unescape(item.get('description', '')).replace('<b>', '').replace('</b>', '')
            if self.exclude_keywords and any(ex in title or ex in description for ex in self.exclude_keywords):
                continue
            
            naver_news_link = item.get('link', '')
            original_link = item.get('originallink', '')
            
            if 'n.news.naver.com' in naver_news_link:
                final_link = naver_news_link
            elif original_link:
                final_link = original_link
            else:
                final_link = naver_news_link

            publisher = "정보 없음"
            try:
                if original_link:
                    parsed_url = urllib.parse.urlparse(original_link)
                    hostname = parsed_url.netloc
                    if 'naver.com' in hostname or 'naver.net' in hostname:
                        publisher = "네이버 뉴스" 
                    else:
                        publisher = hostname.replace('www.', '')
                elif naver_news_link:
                        publisher = "네이버 뉴스"
            except Exception:
                pass 

            processed_news.append({
                'title': title,
                'link': final_link,
                'description': description,
                'pubDate': item.get('pubDate', ''),
                'publisher': publisher 
            })
        
        return {'items': processed_news, 'total': total_results}

# --- 메인 애플리케이션 윈도우 클래스 ---
class NewsScraperApp(QMainWindow):
    """
    실시간 네이버 뉴스 검색 애플리케이션 v18.2
    [v18.2 디버깅 개선사항]
    - 스레드 안전 DB 연결 (스레드별 연결 분리)
    - WAL 모드 활성화로 동시 읽기/쓰기 성능 개선
    - 네트워크 세션 관리 개선 (각 요청마다 세션 생성/정리)
    - Worker 취소 메커니즘 추가
    - 타이머 중복 방지 강화
    - 메모리 누수 방지 개선
    - 예외 처리 강화
    """
    APP_SCHEME = "app"
    ACTION_UNREAD = "unread"
    ACTION_TOGGLE_BOOKMARK = "toggle_bookmark"
    ACTION_SHARE = "share"
    ACTION_OPEN_EXTERNAL = "open_external"
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager(DB_FILE)
        
        self.client_id = ""
        self.client_secret = ""
        self.theme_index = 0
        
        self.active_threads = {}
        self.auto_refresh_timer = None
        
        self.setWindowTitle(f"실시간 뉴스 검색 (네이버 API) v{VERSION}")
        self.setGeometry(100, 100, 900, 750)
        
        self.init_ui()
        self.init_tray_icon()
        QTimer.singleShot(100, self.post_init_setup)

    def post_init_setup(self):
        self.load_config()
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        if not self.client_id or not self.client_secret:
            QMessageBox.information(self, "환영합니다", "네이버 뉴스 스크래퍼를 사용하기 위해 먼저 '설정' 메뉴에서 API 키를 입력해주세요.")
            self.open_settings_dialog()
        
        self.setup_auto_refresh()
        if self.tab_widget.count() > 1:
            self.tab_widget.setCurrentIndex(1)
            self.start_fetching(target_index=1)
        self.redraw_bookmark_tab()

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("실시간 뉴스 검색")
        tray_menu = QMenu()
        show_action = QAction("열기", self)
        quit_action = QAction("종료", self)
        
        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_notification(self, keyword, count):
        """새 뉴스 알림을 표시합니다."""
        if not self.isActiveWindow() or self.isMinimized():
            self.tray_icon.showMessage(
                '새 뉴스 알림', 
                f"'{keyword}'에 {count}개의 새로운 뉴스가 도착했습니다.", 
                QSystemTrayIcon.MessageIcon.Information, 
                3000
            )

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        control_layout = QHBoxLayout()
        self.refresh_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload), " 새로고침")
        self.export_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), " 결과 저장")
        self.settings_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView), " 설정")
        self.open_config_folder_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon), " 설정 폴더")
        self.add_tab_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), "+ 새 탭 추가")
        self.add_tab_button.setObjectName("AddTab")
        
        self.refresh_interval_combo = QComboBox()
        self.refresh_interval_combo.addItems(["10분", "30분", "1시간", "3시간", "6시간", "자동 새로고침 안함"])
        self.refresh_interval_combo.hide()

        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.export_button)
        control_layout.addWidget(self.settings_button)
        control_layout.addWidget(self.open_config_folder_button)
        control_layout.addStretch(1)
        control_layout.addWidget(self.add_tab_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabBar().setMovable(True)
        self.create_bookmark_tab()

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.tab_widget)
        self.statusBar().showMessage("준비 완료.")

        self.refresh_button.clicked.connect(lambda: self.start_fetching())
        self.export_button.clicked.connect(self.export_results)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.open_config_folder_button.clicked.connect(self.open_config_folder)
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.tabBar().tabBarDoubleClicked.connect(self.rename_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def open_settings_dialog(self):
        current_config = {
            "client_id": self.client_id, "client_secret": self.client_secret,
            "refresh_interval_index": self.refresh_interval_combo.currentIndex(),
            "theme_index": self.theme_index
        }
        dialog = SettingsDialog(self, config=current_config, db=self.db)
        
        if dialog.exec():
            new_settings = dialog.get_settings()
            
            if (new_settings["client_id"] and not new_settings["client_secret"]) or \
               (not new_settings["client_id"] and new_settings["client_secret"]):
                QMessageBox.warning(self, "설정 오류", "Client ID와 Secret은 함께 입력하거나 모두 비워두어야 합니다.")
                return

            self.client_id = new_settings["client_id"]
            self.client_secret = new_settings["client_secret"]
            
            if self.refresh_interval_combo.currentIndex() != new_settings["refresh_interval_index"]:
                self.refresh_interval_combo.setCurrentIndex(new_settings["refresh_interval_index"])
                self.update_refresh_interval()

            if self.theme_index != new_settings["theme_index"]:
                self.theme_index = new_settings["theme_index"]
                self.apply_theme()

            self.save_config()
            self.statusBar().showMessage("설정이 저장되었습니다.", 3000)
            if self.client_id and self.client_secret and self.tab_widget.currentIndex() > 0:
                 self.start_fetching()

    def open_config_folder(self):
        config_path = os.path.abspath(CONFIG_FILE)
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(config_dir))

    def on_tab_changed(self, index):
        is_bookmark_tab = (index == 0)
        self.refresh_button.setDisabled(is_bookmark_tab)
        
        current_widget = self.tab_widget.widget(index)
        if not current_widget: return

        if hasattr(current_widget, 'load_more_button'):
            current_widget.load_more_button.setVisible(not is_bookmark_tab)
        
        if hasattr(current_widget, 'new_links') and current_widget.new_links:
            current_widget.new_links.clear()
            if self.tab_widget.tabText(index) != current_widget.original_title:
                self.tab_widget.setTabText(index, current_widget.original_title)
            self.render_tab_content(current_widget)

    def setup_auto_refresh(self):
        """자동 새로고침 타이머 설정"""
        if self.auto_refresh_timer:
            self.auto_refresh_timer.stop()
            self.auto_refresh_timer.deleteLater()
            self.auto_refresh_timer = None
        
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.setSingleShot(False)
        self.auto_refresh_timer.timeout.connect(self.refresh_all_tabs_auto)
        self.update_refresh_interval()

    def refresh_all_tabs_auto(self):
        """모든 탭을 자동으로 새로고침합니다."""
        if not self.active_threads:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 자동 새로고침 시작")
            self.statusBar().showMessage("모든 탭 자동 새로고침 중...")
            
            for i in range(1, self.tab_widget.count()):
                tab_content = self.tab_widget.widget(i)
                if tab_content and hasattr(tab_content, 'original_title'):
                    self.start_fetching(is_auto=True, target_index=i)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 자동 새로고침 건너뜀 (작업 진행 중)")

    def update_refresh_interval(self):
        """새로고침 간격 업데이트"""
        if not self.auto_refresh_timer:
            return
            
        self.auto_refresh_timer.stop()
        current_text = self.refresh_interval_combo.currentText()

        if not current_text:
            self.statusBar().showMessage("자동 새로고침 간격 설정 오류.")
            return

        if "안함" in current_text:
            self.statusBar().showMessage("자동 새로고침이 비활성화되었습니다.")
            return
        
        interval_map = {"분": 60 * 1000, "시간": 60 * 60 * 1000}
        try:
            value_str = "".join(filter(str.isdigit, current_text))
            unit = current_text[-1]
            value = int(value_str)
            
            milliseconds = value * interval_map[unit]
            self.auto_refresh_timer.start(milliseconds)
            self.statusBar().showMessage(f"모든 탭 자동 새로고침 간격이 {current_text}으로 설정되었습니다.")
            print(f"자동 새로고침 타이머: {milliseconds}ms ({current_text})")
        except (ValueError, KeyError, IndexError) as e:
            print(f"자동 새로고침 간격 설정 오류: {e}")
            self.statusBar().showMessage("자동 새로고침 간격 설정 오류.")

    def _parse_keywords(self, text):
        parts = [p.strip() for p in text.split('-') if p.strip()]
        return parts[0], parts[1:] if len(parts) > 1 else []

    def load_config(self):
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.loads(f.read() or '{}')

            app_settings = config.get("app_settings", {})
            self.client_id = app_settings.get("client_id", "")
            self.client_secret = app_settings.get("client_secret", "")
            
            if geometry_data := app_settings.get("window_geometry"):
                self.restoreGeometry(QByteArray.fromBase64(geometry_data.encode('ascii')))

            refresh_index = app_settings.get("refresh_interval_index", 2)
            if not (0 <= refresh_index < self.refresh_interval_combo.count()):
                refresh_index = 2
            self.refresh_interval_combo.setCurrentIndex(refresh_index)
            
            self.theme_index = app_settings.get("theme_index", 0)
            self.apply_theme()

            for keyword in config.get("tabs", ["방심위", "과방위"]):
                self.create_tab(keyword)
        except (json.JSONDecodeError, KeyError) as e:
            QMessageBox.critical(self, "설정 파일 오류", f"설정 파일을 불러오는 중 오류: {e}\n기본 설정으로 시작합니다.")

    def save_config(self):
        try:
            tabs_to_save = [
                self.tab_widget.widget(i).original_title
                for i in range(1, self.tab_widget.count())
                if hasattr(self.tab_widget.widget(i), 'original_title')
            ]
            config = {
                "app_settings": {
                    "refresh_interval_index": self.refresh_interval_combo.currentIndex(),
                    "theme_index": self.theme_index,
                    "client_id": self.client_id, "client_secret": self.client_secret,
                    "window_geometry": self.saveGeometry().toBase64().data().decode('ascii')
                },
                "tabs": tabs_to_save
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.statusBar().showMessage(f"설정 파일 저장 오류: {e}")

    def apply_theme(self):
        stylesheet = DARK_STYLESHEET if self.theme_index == 1 else LIGHT_STYLESHEET
        self.setStyleSheet(stylesheet)
        self.redraw_all_tabs()

    def create_bookmark_tab(self):
        tab_content = self.create_tab_content_widget()
        tab_content.original_title = "북마크"
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon)
        index = self.tab_widget.insertTab(0, tab_content, icon, "북마크")
        self.tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
        tab_content.load_more_button.hide()

    def create_tab_content_widget(self):
        tab_content_widget = QWidget()
        layout = QVBoxLayout(tab_content_widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        top_bar_layout = QHBoxLayout()
        filter_input = QLineEdit(placeholderText="결과 내에서 필터링...")
        sort_combo = QComboBox()
        sort_combo.addItems(["최신순", "오래된순"])
        top_bar_layout.addWidget(filter_input)
        top_bar_layout.addWidget(sort_combo)
        
        browser = QTextBrowser(openExternalLinks=False)
        browser.anchorClicked.connect(self.handle_link_click)

        bottom_bar_layout = QHBoxLayout()
        load_more_button = QPushButton("더 불러오기")
        mark_all_read_button = QPushButton("모두 읽음으로")
        scroll_top_button = QPushButton("맨 위로")
        last_updated_label = QLabel("업데이트 대기 중")
        bottom_bar_layout.addWidget(load_more_button)
        bottom_bar_layout.addWidget(mark_all_read_button)
        bottom_bar_layout.addWidget(scroll_top_button)
        bottom_bar_layout.addStretch()
        bottom_bar_layout.addWidget(last_updated_label)

        layout.addLayout(top_bar_layout)
        layout.addWidget(browser)
        layout.addLayout(bottom_bar_layout)
        
        tab_content_widget.browser = browser
        tab_content_widget.filter_input = filter_input
        tab_content_widget.last_updated_label = last_updated_label
        tab_content_widget.sort_combo = sort_combo
        tab_content_widget.load_more_button = load_more_button
        tab_content_widget.scroll_top_button = scroll_top_button
        tab_content_widget.new_links = set()
        tab_content_widget.original_title = ""
        tab_content_widget.total_results = 0

        filter_input.textChanged.connect(lambda: self.on_filter_changed(tab_content_widget))
        sort_combo.currentIndexChanged.connect(lambda: self.render_tab_content(tab_content_widget))
        mark_all_read_button.clicked.connect(lambda: self.mark_all_as_read(tab_content_widget))
        load_more_button.clicked.connect(lambda: self.start_fetching(is_load_more=True))
        scroll_top_button.clicked.connect(lambda: browser.verticalScrollBar().setValue(0))
        
        return tab_content_widget
    
    def on_filter_changed(self, tab_content):
        """필터 입력 시 시각적 피드백을 제공합니다."""
        filter_text = tab_content.filter_input.text()
        if filter_text:
            tab_content.filter_input.setObjectName("FilterActive")
        else:
            tab_content.filter_input.setObjectName("")
        
        tab_content.filter_input.setStyle(tab_content.filter_input.style())
        self.render_tab_content(tab_content)
    
    def mark_all_as_read(self, tab_content):
        self.db.mark_all_as_read(tab_content.original_title)
        tab_content.new_links.clear()
        current_index = self.tab_widget.indexOf(tab_content)
        if current_index >= 0:
            self.tab_widget.setTabText(current_index, tab_content.original_title)
        self.render_tab_content(tab_content)
        self.statusBar().showMessage("모든 기사를 읽음으로 처리했습니다.", 3000)

    def create_tab(self, keyword):
        tab_content = self.create_tab_content_widget()
        tab_content.original_title = keyword
        index = self.tab_widget.addTab(tab_content, keyword)
        self.tab_widget.setCurrentIndex(index)
        return tab_content

    def handle_link_click(self, url):
        url_string = url.toString()
        scheme = url.scheme()
        
        if scheme == self.APP_SCHEME:
            action = url.host()
            data = url.path().lstrip('/') 

            if action == self.ACTION_UNREAD:
                self.db.set_read_status(data, False)
                self.redraw_current_tab()
            elif action == self.ACTION_TOGGLE_BOOKMARK:
                self.db.toggle_bookmark(data)
                self.redraw_all_tabs()
            elif action == self.ACTION_OPEN_EXTERNAL:
                decoded_link = urllib.parse.unquote(data)
                QDesktopServices.openUrl(QUrl(decoded_link))
            elif action == self.ACTION_SHARE:
                try:
                    decoded_news_str = urllib.parse.unquote(data)
                    news_item = json.loads(decoded_news_str)
                    share_text = f"{news_item['title']}\n{news_item['link']}"
                    QApplication.clipboard().setText(share_text)
                    self.statusBar().showMessage("기사 제목과 링크가 클립보드에 복사되었습니다.", 3000)
                except Exception as e:
                    QMessageBox.critical(self, "공유 오류", f"공유 데이터 처리 중 오류: {e}")
        
        else:
            self.db.set_read_status(url_string, True)
            QDesktopServices.openUrl(url)
            self.redraw_current_tab()

    def redraw_all_tabs(self):
        for i in range(self.tab_widget.count()):
            if tab_content := self.tab_widget.widget(i):
                self.render_tab_content(tab_content)

    def redraw_current_tab(self):
        if current_tab := self.tab_widget.currentWidget():
            self.render_tab_content(current_tab)

    def redraw_bookmark_tab(self):
        if bookmark_tab := self.tab_widget.widget(0):
            self.render_tab_content(bookmark_tab)

    def render_tab_content(self, tab_content):
        if not tab_content: return

        keyword = tab_content.original_title
        is_bookmark_tab = (keyword == "북마크")
        filter_text = tab_content.filter_input.text().lower()
        sort_order = tab_content.sort_combo.currentText()
        
        if is_bookmark_tab:
            display_items = self.db.get_bookmarks(filter_text, sort_order)
        else:
            display_items = self.db.get_news(keyword, filter_text, sort_order)
        
        self.render_html(tab_content, display_items, filter_text)
        
        if self.tab_widget.currentWidget() == tab_content and not is_bookmark_tab:
            loaded_count = len(display_items)
            total_api_count = tab_content.total_results
            unread_count = self.db.get_unread_count(keyword)
            
            status_msg = f"'{keyword}': 총 {total_api_count}개 중 {loaded_count}개 표시"
            if unread_count > 0:
                status_msg += f" (안 읽음: {unread_count}개)"
            if filter_text:
                status_msg += f" [필터 적용됨]"
            self.statusBar().showMessage(status_msg)
        elif is_bookmark_tab:
             self.statusBar().showMessage(f"북마크 {len(display_items)}개 표시됨")

    def rename_tab(self, index):
        if index == 0: return
        tab_content = self.tab_widget.widget(index)
        old_name = tab_content.original_title

        text, ok = QInputDialog.getText(self, '탭 이름 변경', '새 키워드를 입력하세요:', text=old_name)
        if ok and text and text != old_name:
            tab_content.original_title = text
            self.tab_widget.setTabText(index, text)
            self.start_fetching(target_index=index)

    def add_new_tab(self):
        text, ok = QInputDialog.getText(self, '새 탭 추가', '검색 키워드(예: "정확한 검색어" -제외어)')
        if ok and text:
            for i in range(1, self.tab_widget.count()):
                if self.tab_widget.widget(i).original_title == text:
                    self.tab_widget.setCurrentIndex(i)
                    return
            self.create_tab(text)
            self.start_fetching()

    def close_tab(self, index):
        if index == 0: return
        
        tab_content = self.tab_widget.widget(index)
        if tab_content and tab_content.original_title in self.active_threads:
            thread, worker = self.active_threads.pop(tab_content.original_title)
            if worker:
                worker.cancel()
            if thread:
                thread.quit()
                thread.wait(1000)
        
        if widget := self.tab_widget.widget(index):
            widget.deleteLater()
        self.tab_widget.removeTab(index)

    def start_fetching(self, is_auto=False, target_index=None, is_load_more=False):
        idx = target_index if target_index is not None else self.tab_widget.currentIndex()
        if idx < 1: return
        tab_content = self.tab_widget.widget(idx)
        if not tab_content: return
        
        tab_key = tab_content.original_title

        if tab_key in self.active_threads:
            if not is_auto:
                self.statusBar().showMessage(f"'{tab_key}' 탭은 이미 새로고침 중입니다.", 2000)
            return

        if not self.client_id or not self.client_secret:
            if not is_auto: 
                QMessageBox.warning(self, "API 키 필요", "뉴스 검색을 위해 '설정' 메뉴에서 키를 먼저 설정해주세요.")
            self.statusBar().showMessage("API 키가 설정되지 않았습니다.")
            return

        keyword, exclude_keywords = self._parse_keywords(tab_key)
        
        loaded_count = self.db.get_news_count(tab_key)
        start_index = loaded_count + 1 if is_load_more else 1

        if is_load_more and (loaded_count >= tab_content.total_results or start_index > 901):
            self.statusBar().showMessage("더 이상 불러올 뉴스가 없습니다.")
            return

        self.refresh_button.setEnabled(False)
        tab_content.load_more_button.setEnabled(False)
        status_msg = f"'{keyword}' 뉴스 {'추가 로딩 중' if is_load_more else '검색 중'}..."
        self.statusBar().showMessage(status_msg)
        
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        
        if not is_load_more and not is_auto:
            loading_color = "#AAAAAA" if self.theme_index == 1 else "#888"
            tab_content.browser.setHtml(f"<div style='padding: 20px; text-align: center; color: {loading_color}; font-family: 맑은 고딕;'>{status_msg}</div>")

        thread = QThread()
        worker = Worker(keyword, exclude_keywords, self.client_id, self.client_secret, start=start_index)
        worker.moveToThread(thread)

        worker.finished.connect(lambda r, key=tab_key, ilm=is_load_more, ia=is_auto: self.update_results(r, key, ilm, ia))
        worker.error.connect(lambda msg, key=tab_key: self.handle_error(msg, key))
        
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        self.active_threads[tab_key] = (thread, worker)
        thread.start()

    def _finalize_fetch_job(self, tab_key):
        """스레드 작업 완료 후 정리"""
        if tab_key in self.active_threads:
            thread, worker = self.active_threads.pop(tab_key)
            if thread and thread.isRunning():
                thread.quit()
                thread.wait(500)

        if not self.active_threads:
            self.refresh_button.setEnabled(True)
            self.progress_bar.hide()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def find_tab_by_key(self, tab_key):
        for i in range(1, self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if widget and hasattr(widget, 'original_title') and widget.original_title == tab_key:
                return widget, i
        return None, -1

    def update_results(self, result_dict, tab_key, is_load_more, is_auto):
        try:
            target_tab_content, tab_index = self.find_tab_by_key(tab_key)
            if not target_tab_content:
                return
                
            news_items = result_dict['items']
            total = result_dict['total']
            target_tab_content.total_results = total
            
            added_count = 0
            if news_items:
                added_count = self.db.add_news_items(tab_key, news_items)
                
                if added_count > 0 and not is_load_more:
                    new_links = {item['link'] for item in news_items}
                    target_tab_content.new_links.update(new_links)
                    
                    if tab_index >= 0:
                        new_count = len(target_tab_content.new_links)
                        self.tab_widget.setTabText(tab_index, f"{tab_key} ({new_count})")
                    
                    if is_auto:
                        self.show_notification(tab_key, added_count)
            
            if self.tab_widget.currentWidget() == target_tab_content:
                self.render_tab_content(target_tab_content)
                target_tab_content.last_updated_label.setText(f"마지막 새로고침: {datetime.now().strftime('%H:%M:%S')}")
            
            current_total = self.db.get_news_count(tab_key)
            can_load_more = current_total < total and current_total < 1000
            target_tab_content.load_more_button.setEnabled(can_load_more)
            
            if not is_auto:
                result_msg = f"'{tab_key}': "
                if is_load_more:
                    result_msg += f"{added_count}개 기사를 추가로 불러왔습니다."
                else:
                    result_msg += f"총 {total}개 중 {current_total}개 로드됨"
                    if added_count > 0:
                        result_msg += f" (신규 {added_count}개)"
                self.statusBar().showMessage(result_msg, 5000)
        except Exception as e:
            print(f"결과 업데이트 오류: {e}")
        finally:
            self._finalize_fetch_job(tab_key)
    
    def _create_news_item_html(self, news, keyword, filter_text):
        is_read = news.get('is_read', False)
        is_bookmarked = news.get('is_bookmarked', False)

        read_class = " read" if is_read else ""
        
        title_prefix = "⭐ " if is_bookmarked else ""
        title_html = html.escape(news['title'])
        desc_html = html.escape(news['description'])
        
        highlight_keyword = keyword.strip('"')
        if highlight_keyword:
            highlight_color = "#FFF3CD" if self.theme_index == 0 else "#6F602A"
            highlight_text_color = "#000000" if self.theme_index == 0 else "#FFFFFF"
            highlight = f"<span style='background-color: {highlight_color}; color: {highlight_text_color}; padding: 2px 4px; border-radius: 3px;'>{html.escape(highlight_keyword)}</span>"
            title_html = title_html.replace(html.escape(highlight_keyword), highlight)
            desc_html = desc_html.replace(html.escape(highlight_keyword), highlight)
            
        if filter_text:
            filter_highlight_color = "#FFD1D1" if self.theme_index == 0 else "#7A3E3E"
            filter_text_color = "#000000" if self.theme_index == 0 else "#FFFFFF"
            for f_word in filter_text.split():
                if not f_word: continue
                f_word_html = html.escape(f_word)
                filter_highlight = f"<span style='background-color: {filter_highlight_color}; color: {filter_text_color}; padding: 1px 2px; border-bottom: 1px dashed red;'>{f_word_html}</span>"
                title_html = title_html.replace(f_word_html, filter_highlight)
                desc_html = desc_html.replace(f_word_html, filter_highlight)

        try:
            formatted_date = parsedate_to_datetime(news['pubDate']).strftime('%Y-%m-%d %H:%M')
        except: 
            formatted_date = "날짜 정보 없음"

        news_json = json.dumps(news, ensure_ascii=False)
        encoded_news = urllib.parse.quote(news_json)
        encoded_link = urllib.parse.quote(news['link'], safe='')

        share_url = f"{self.APP_SCHEME}://{self.ACTION_SHARE}/{encoded_news}"
        external_url = f"{self.APP_SCHEME}://{self.ACTION_OPEN_EXTERNAL}/{encoded_link}"
        unread_url = f"{self.APP_SCHEME}://{self.ACTION_UNREAD}/{news['link']}"
        bookmark_url = f"{self.APP_SCHEME}://{self.ACTION_TOGGLE_BOOKMARK}/{news['link']}"
        
        bookmark_text = "[북마크 해제]" if is_bookmarked else "[북마크]"
        bookmark_color_style = "color: #DC3545;" if is_bookmarked else "color: #17A2B8;"
        
        actions_html = f"<a href='{share_url}'>[공유]</a> "
        actions_html += f"<a href='{external_url}'>[외부에서 열기]</a> "
        if is_read: 
            actions_html += f"<a href='{unread_url}'>[안 읽음]</a> "
        actions_html += f"<a href='{bookmark_url}' style='{bookmark_color_style}'>{bookmark_text}</a>"
        
        publisher_info = f"{news.get('publisher', '정보 없음')}"
        description_p = f'<p class="description">{desc_html}</p>' if desc_html else ""

        return f"""
        <div class="news-item{read_class}">
            <div><a href="{news['link']}" class="title-link">{title_prefix}{title_html}</a></div>
            <table width="100%" style="font-size: 9pt;"><tr>
                <td class="meta-info">{publisher_info} - {formatted_date}</td>
                <td class="actions" align="right">{actions_html}</td>
            </tr></table>
            {description_p}
        </div>"""

    def render_html(self, tab_content, news_items, filter_text):
        browser = tab_content.browser
        keyword, _ = self._parse_keywords(tab_content.original_title)
        
        if not news_items:
            msg = "북마크된 기사가 없습니다." if tab_content.original_title == "북마크" else "표시할 뉴스 기사가 없습니다."
            msg_color = "#AAAAAA" if self.theme_index == 1 else "#888"
            browser.setHtml(f"<div style='padding: 20px; text-align: center; color: {msg_color}; font-family: 맑은 고딕;'>{msg}</div>")
            return

        if self.theme_index == 0:
            style = """<style>
                body { font-family: '맑은 고딕'; margin: 5px; color: #000000; }
                a { text-decoration: none; color: #007BFF; transition: color 0.2s; }
                a:hover { color: #0056b3; }
                .news-item { border: 1px solid #E9ECEF; border-radius: 8px; padding: 15px; margin-bottom: 10px; background-color: #FFFFFF; transition: box-shadow 0.2s; }
                .news-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
                .news-item.read { background-color: #F8F9FA; opacity: 0.7; }
                .title-link { font-size: 12pt; font-weight: bold; color: #212529; }
                .meta-info { color: #6C757D; }
                .description { margin-top: 10px; line-height: 1.6; color: #495057;}
                .actions { text-align: right; }
            </style>"""
        else:
            style = """<style>
                body { font-family: '맑은 고딕'; margin: 5px; color: #E0E0E0; }
                a { text-decoration: none; color: #58A6FF; transition: color 0.2s; }
                a:hover { color: #79C0FF; }
                .news-item { border: 1px solid #4A4A4A; border-radius: 8px; padding: 15px; margin-bottom: 10px; background-color: #3C3C3C; transition: box-shadow 0.2s; }
                .news-item:hover { box-shadow: 0 2px 8px rgba(255,255,255,0.05); }
                .news-item.read { background-color: #313131; opacity: 0.6; }
                .title-link { font-size: 12pt; font-weight: bold; color: #E0E0E0; }
                .meta-info { color: #AAAAAA; }
                .description { margin-top: 10px; line-height: 1.6; color: #CCCCCC;}
                .actions { text-align: right; }
            </style>"""

        html_body = "".join([self._create_news_item_html(news, keyword, filter_text) for news in news_items])
        html_content = f"<html><head>{style}</head><body>{html_body}</body></html>"
        browser.setHtml(html_content)

    def _write_export_file(self, filepath, data_to_export, keyword):
        """내보내기 파일 쓰기 로직"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== {keyword} 뉴스 검색 결과 ===\n")
                f.write(f"내보내기 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"총 {len(data_to_export)}개 기사\n\n")
                f.write("="*80 + "\n\n")
                
                for i, news in enumerate(data_to_export, 1):
                    f.write(f"[{i}] {news['title']}\n")
                    f.write(f"    출처: {news.get('publisher', '정보 없음')}\n")
                    f.write(f"    링크: {news['link']}\n")
                    f.write(f"    요약: {news['description']}\n")
                    f.write(f"    발행일: {news.get('pubDate', '정보 없음')}\n")
                    if news.get('is_bookmarked'):
                        f.write(f"    상태: 북마크됨\n")
                    f.write("\n" + "-"*80 + "\n\n")
            
            self.statusBar().showMessage(f"'{os.path.basename(filepath)}' 파일로 저장 완료 ({len(data_to_export)}개 기사)", 5000)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}")

    def export_results(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0: return
        
        tab_content = self.tab_widget.widget(current_index)
        keyword = tab_content.original_title
        filter_text = tab_content.filter_input.text()
        sort_order = "최신순"
        
        if keyword == "북마크":
            all_data = self.db.get_bookmarks("", sort_order)
        else:
            all_data = self.db.get_news(keyword, "", sort_order)

        if not all_data:
            QMessageBox.information(self, "알림", "저장할 뉴스 데이터가 없습니다.")
            return

        data_to_export = all_data

        if filter_text:
            if keyword == "북마크":
                filtered_data = self.db.get_bookmarks(filter_text, sort_order)
            else:
                filtered_data = self.db.get_news(keyword, filter_text, sort_order)
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("내보내기 옵션")
            msg_box.setText(f"'{filter_text}' 필터가 활성화되어 있습니다. 무엇을 내보내시겠습니까?")
            filtered_btn = msg_box.addButton(f"필터링된 결과만 ({len(filtered_data)}개)", QMessageBox.ButtonRole.ActionRole)
            all_btn = msg_box.addButton(f"'{keyword}' 전체 결과 ({len(all_data)}개)", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.exec()
            
            if msg_box.clickedButton() == filtered_btn:
                data_to_export = filtered_data
            elif msg_box.clickedButton() == all_btn:
                data_to_export = all_data
            else:
                return
        
        if not data_to_export:
             QMessageBox.information(self, "알림", "선택한 조건으로 저장할 뉴스 데이터가 없습니다.")
             return

        default_filename = f"{keyword.replace(' ', '_').replace('-', '_')}_뉴스_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath, _ = QFileDialog.getSaveFileName(self, "결과 저장", default_filename, "Text Files (*.txt)")
        if filepath:
            self._write_export_file(filepath, data_to_export, keyword)

    def handle_error(self, error_message, tab_key):
        """에러 핸들링"""
        print(f"[오류] {tab_key}: {error_message}")
        
        if not error_message.startswith("API"):
            QMessageBox.warning(self, f"'{tab_key}' 탭 갱신 오류", error_message)
        
        self.statusBar().showMessage(f"'{tab_key}' 새로고침 실패. 나중에 다시 시도해주세요.", 5000)
        
        target_tab_content, _ = self.find_tab_by_key(tab_key)
        if target_tab_content:
            target_tab_content.load_more_button.setEnabled(True)
            
        self._finalize_fetch_job(tab_key)

    def closeEvent(self, event):
        """앱 종료 시 정리 작업"""
        print("애플리케이션 종료 중...")
        
        # 자동 새로고침 타이머 정리
        if self.auto_refresh_timer:
            self.auto_refresh_timer.stop()
            self.auto_refresh_timer.deleteLater()
            self.auto_refresh_timer = None
        
        # 모든 활성 스레드 정리
        if self.active_threads:
            self.statusBar().showMessage("백그라운드 작업을 종료하는 중...")
            print(f"활성 스레드 {len(self.active_threads)}개 정리 중...")
            
            for key, (thread, worker) in list(self.active_threads.items()):
                if worker:
                    worker.cancel()
                if thread and thread.isRunning():
                    thread.quit()
                    if not thread.wait(3000):
                        print(f"경고: {key} 스레드 강제 종료")
                        thread.terminate()
                        thread.wait()
            
            self.active_threads.clear()
        
        # 설정 저장
        self.save_config()
        
        # DB 연결 정리
        try:
            self.db.close()
        except Exception as e:
            print(f"DB 종료 오류: {e}")
        
        print("애플리케이션 종료 완료")
        super().closeEvent(event)

# --- 전역 예외 처리 ---
def handle_exception(exc_type, exc_value, exc_traceback):
    """처리되지 않은 모든 예외를 로깅하고 사용자에게 알립니다."""
    if exc_type is KeyboardInterrupt:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(error_msg)
    
    simple_msg = f"예기치 않은 오류가 발생했습니다:\n{exc_type.__name__}: {str(exc_value)}"
    
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("오류 발생")
    msg_box.setText(simple_msg)
    msg_box.setDetailedText(error_msg)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()

def main():
    """애플리케이션의 메인 진입점"""
    sys.excepthook = handle_exception
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("실시간 뉴스 검색")
    app.setOrganizationName("NewsScraperApp")
    
    main_window = NewsScraperApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
