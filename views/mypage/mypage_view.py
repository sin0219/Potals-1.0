import flet as ft
import sqlite3
import os
from db import get_connection

def mypage_view(page: ft.Page):
    # ログインユーザー情報を取得
    # 修正前: logged_user_name = page.client_storage.get("mypage_user_name")
    # 修正後:
    logged_user_name = page.session.get("mypage_user_name")
    
    if not logged_user_name:
        # ログインしていない場合はトップへ
        page.go("/")
        return ft.Text("ログインしてください", color="red")
    
    page.title = f"{logged_user_name} さんのマイページ"
    
    # タブの状態管理
    current_tab_index = ft.Ref[int]()
    current_tab_index.value = 0
    
    result_list = ft.Column(spacing=10, scroll="auto", expand=True)
    
    def load_unapproved_items(tab_index):
        """未認証のアイテムを取得"""
        conn = get_connection()
        cursor = conn.cursor()
        results = []
        
        try:
            if tab_index == 0:  # 日報タブ
                cursor.execute("""
                    SELECT rowid, updated_at, time, updated_by, detail, approved_by
                    FROM daily
                    ORDER BY updated_at DESC
                """)
                all_items = cursor.fetchall()
                
                # approved_byにログインユーザー名が含まれていないものを抽出
                for item in all_items:
                    rowid, updated_at, time, updated_by, detail, approved_by = item
                    approved_list = [name.strip() for name in approved_by.split(",") if name.strip()]
                    if logged_user_name not in approved_list:
                        results.append((rowid, updated_at, time, updated_by, detail, len(approved_list)))
                        
            else:  # 引継タブ
                cursor.execute("""
                    SELECT id, updated_at, updated_by, title, detail, approved_by, origin
                    FROM handovers
                    ORDER BY updated_at DESC
                """)
                all_items = cursor.fetchall()
                
                # approved_byにログインユーザー名が含まれていないものを抽出
                for item in all_items:
                    hid, updated_at, updated_by, title, detail, approved_by, origin = item
                    approved_list = [name.strip() for name in approved_by.split(",") if name.strip()]
                    if logged_user_name not in approved_list:
                        results.append((hid, updated_at, updated_by, title, detail, len(approved_list), origin))
                        
        except Exception as e:
            print(f"データ取得エラー: {e}")
        finally:
            conn.close()
            
        return results
    
    def build_list():
        """リストを構築"""
        result_list.controls.clear()
        
        tab_name = "日報" if current_tab_index.value == 0 else "引継"
        items = load_unapproved_items(current_tab_index.value)
        
        result_list.controls.append(
            ft.Text(f"未認証の{tab_name}: {len(items)}件", size=18, weight="bold")
        )
        
        if items:
            for item in items:
                if current_tab_index.value == 0:  # 日報
                    rowid, updated_at, time, updated_by, detail, approver_count = item
                    detail_preview = detail[:80] + "..." if len(detail) > 80 else detail
                    
                    result_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text(f"📅 {updated_at.split()[0]}", size=14, weight="bold"),
                                        ft.Text(f"🕐 {time}", size=12, color="grey"),
                                    ], spacing=10),
                                    ft.Text(f"更新者: {updated_by}", size=12, color="grey"),
                                    ft.Text(detail_preview, size=14),
                                    ft.Row([
                                        ft.Icon("check_circle", size=16, color="green"),
                                        ft.Text(f"{approver_count}名認証済", size=12, color="green"),
                                    ], spacing=5),
                                ], spacing=8),
                                padding=15,
                                on_click=lambda e, r=rowid: page.go(f"/daily/detail?id={r}&from=/mypage")
                            ),
                            elevation=2
                        )
                    )
                else:  # 引継
                    hid, updated_at, updated_by, title, detail, approver_count, origin = item
                    detail_preview = detail[:80] + "..." if len(detail) > 80 else detail
                    
                    # 発信元の色を取得
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT color FROM origins WHERE name = ?", (origin,))
                    origin_color_row = cursor.fetchone()
                    conn.close()
                    origin_color = origin_color_row[0] if origin_color_row else "#CCCCCC"
                    
                    origin_label = ft.Container(
                        content=ft.Text(origin or "不明", size=10, color="white"),
                        width=60,
                        height=20,
                        alignment=ft.alignment.center,
                        border_radius=10,
                        bgcolor=origin_color,
                    )
                    
                    result_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        origin_label,
                                        ft.Text(title, size=16, weight="bold", expand=True),
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Text(f"📅 {updated_at}", size=12, color="grey"),
                                        ft.Text(f"更新者: {updated_by}", size=12, color="grey"),
                                    ], alignment="space_between"),
                                    ft.Text(detail_preview, size=14),
                                    ft.Row([
                                        ft.Icon("check_circle", size=16, color="green"),
                                        ft.Text(f"{approver_count}名認証済", size=12, color="green"),
                                    ], spacing=5),
                                ], spacing=8),
                                padding=15,
                                on_click=lambda e, h=hid: page.go(f"/handover_detail/{h}?from=/mypage")
                            ),
                            elevation=2
                        )
                    )
        else:
            result_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("check_circle_outline", size=64, color="green"),
                        ft.Text(f"未認証の{tab_name}はありません", size=16, color="grey"),
                        ft.Text("素晴らしい！すべて確認済みです", size=14, color="grey"),
                    ], horizontal_alignment="center", spacing=10),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        
        page.update()
    
    def on_tab_change(e):
        """タブ切り替え"""
        current_tab_index.value = e.control.selected_index
        build_list()
    
    def on_logout(e):
        """ログアウト"""
        # 修正前: page.client_storage.remove("mypage_user_name")
        # 修正後:
        page.session.remove("mypage_user_name")
        page.go("/")
    
    # ヘッダー部分
    header = ft.Container(
        content=ft.Row([
            ft.Icon("person", size=40, color="#3b82f6"),
            ft.Column([
                ft.Text(f"{logged_user_name} さん", size=24, weight="bold"),
                ft.Text("マイページ", size=16, color="grey"),
            ], spacing=0),
            ft.Container(expand=True),
            ft.TextButton("ログアウト", icon="logout", on_click=on_logout),
        ], alignment="start", vertical_alignment="center"),
        padding=20,
        bgcolor="#f0f9ff",
        border_radius=10,
    )
    
    # タブ
    tabs = ft.Tabs(
        tabs=[
            ft.Tab(text="📋 日報", icon="assignment"),
            ft.Tab(text="📑 引継", icon="swap_horiz")
        ],
        on_change=on_tab_change,
        selected_index=0,
    )
    
    # 戻るボタン
    back_button = ft.ElevatedButton(
        "トップに戻る",
        icon="home",
        on_click=lambda e: page.go("/")
    )
    
    # 初期表示
    build_list()
    
    return ft.Container(
        content=ft.Column([
            header,
            ft.Divider(),
            tabs,
            ft.Container(
                content=result_list,
                expand=True,
                padding=10,
            ),
            ft.Divider(),
            back_button,
        ], spacing=10, expand=True),
        padding=20,
        expand=True,
    )