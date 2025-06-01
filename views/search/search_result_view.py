import flet as ft
import sqlite3
import urllib.parse
import math
from db import get_connection

def search_result_view(page: ft.Page):
    page.title = "検索結果"
    page.scroll = "auto"
    page.padding = 20

    # URLからキーワードを取得
    parsed = urllib.parse.urlparse(page.route)
    params = urllib.parse.parse_qs(parsed.query)
    keyword = params.get("keyword", [""])[0]

    # タイトル部分
    title = ft.Text(f"検索結果: 「{keyword}」", size=24, weight="bold")
    
    # 戻るボタン
    back_button = ft.ElevatedButton(
        "トップに戻る", 
        on_click=lambda e: page.go("/"),
        icon="home"
    )

    # フィルター状態
    sort_descending = ft.Ref[bool]()
    sort_descending.value = True
    current_tab_index = ft.Ref[int]()
    current_tab_index.value = 0

    # ページング設定
    items_per_page = 10
    current_page = ft.Ref[int]()
    current_page.value = 1

    result_list = ft.Column(spacing=10)
    scrollable_area = ft.Container(
        content=ft.Column(controls=[result_list], scroll="auto", expand=True),
        height=500,
        expand=True
    )

    # 並び替えのアイコンボタン
    sort_button = ft.IconButton(
        icon="arrow_downward",
        tooltip="更新日付で並び替え",
        on_click=lambda e: toggle_sort()
    )

    def toggle_sort():
        sort_descending.value = not sort_descending.value
        sort_button.icon = "arrow_downward" if sort_descending.value else "arrow_upward"
        apply_filter()
        page.update()

    def load_results(tab_index):
        if not keyword:  # キーワードが空の場合は何も検索しない
            return []
            
        conn = get_connection()
        cursor = conn.cursor()

        results = []

        try:
            order = "DESC" if sort_descending.value else "ASC"
            
            if tab_index == 0:  # 日報タブ
                cursor.execute(f"""
                    SELECT rowid, updated_at, updated_by, detail 
                    FROM daily 
                    WHERE detail LIKE ? OR updated_by LIKE ?
                    ORDER BY updated_at {order}
                """, (f"%{keyword}%", f"%{keyword}%"))
                results = cursor.fetchall()
            else:  # 引継タブ
                cursor.execute(f"""
                    SELECT id, updated_at, updated_by, title, detail 
                    FROM handovers 
                    WHERE title LIKE ? OR detail LIKE ? OR updated_by LIKE ?
                    ORDER BY updated_at {order}
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
                results = cursor.fetchall()
        except Exception as e:
            print(f"検索エラー: {e}")
        finally:
            conn.close()

        return results

    def apply_filter():
        nonlocal search_data, total_pages
        current_page.value = 1
        search_data = load_results(current_tab_index.value)
        total_pages = max(1, math.ceil(len(search_data) / items_per_page))
        build_page()
        pagination_row.controls = page_controls().controls
        page.update()

    def build_page():
        result_list.controls.clear()
        
        if not keyword:
            result_list.controls.append(
                ft.Text("検索キーワードが指定されていません", color="red")
            )
            page.update()
            return

        start = (current_page.value - 1) * items_per_page
        end = start + items_per_page
        page_data = search_data[start:end]

        tab_name = "日報" if current_tab_index.value == 0 else "引継"
        result_list.controls.append(
            ft.Text(f"{tab_name}から {len(search_data)} 件ヒット（{start + 1}-{min(end, len(search_data))}件目を表示）", 
                   size=16, weight="bold")
        )

        if page_data:
            for row in page_data:
                if current_tab_index.value == 0:
                    detail_preview = row[3][:100] + "..." if len(row[3]) > 100 else row[3]
                    result_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text(f"更新日: {row[1]}", size=12, color="grey"),
                                        ft.Text(f"更新者: {row[2]}", size=12, color="grey"),
                                    ], alignment="space_between"),
                                    ft.Text(detail_preview, size=14),
                                ], spacing=5),
                                padding=15,
                                on_click=lambda e, r=row: page.go(f"/search_daily?id={r[0]}&keyword={keyword}")
                            ),
                            elevation=2
                        )
                    )
                else:
                    detail_preview = row[4][:100] + "..." if len(row[4]) > 100 else row[4]
                    result_list.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text(f"タイトル: {row[3]}", size=16, weight="bold"),
                                    ft.Row([
                                        ft.Text(f"更新日: {row[1]}", size=12, color="grey"),
                                        ft.Text(f"更新者: {row[2]}", size=12, color="grey"),
                                    ], alignment="space_between"),
                                    ft.Text(detail_preview, size=14),
                                ], spacing=5),
                                padding=15,
                                on_click=lambda e, r=row: page.go(f"/search_handover/{r[0]}?keyword={keyword}")
                            ),
                            elevation=2
                        )
                    )
        else:
            tab_name = "日報" if current_tab_index.value == 0 else "引継"
            result_list.controls.append(
                ft.Text(f"該当する{tab_name}が見つかりませんでした", color="grey")
            )
        
        page.update()

    def page_controls():
        return ft.Row(
            controls=[
                ft.IconButton(icon="first_page", tooltip="先頭", 
                            on_click=lambda e: change_page(1), 
                            disabled=current_page.value == 1),
                ft.IconButton(icon="chevron_left", tooltip="前へ", 
                            on_click=lambda e: change_page(current_page.value - 1), 
                            disabled=current_page.value == 1),
                ft.Text(f"{current_page.value} / {total_pages}", size=14, weight="bold"),
                ft.IconButton(icon="chevron_right", tooltip="次へ", 
                            on_click=lambda e: change_page(current_page.value + 1), 
                            disabled=current_page.value == total_pages),
                ft.IconButton(icon="last_page", tooltip="最後", 
                            on_click=lambda e: change_page(total_pages), 
                            disabled=current_page.value == total_pages),
            ],
            alignment="center",
            spacing=5,
        )

    def change_page(new_page):
        if 1 <= new_page <= total_pages:
            current_page.value = new_page
            build_page()
            pagination_row.controls = page_controls().controls
            page.update()

    def on_tab_change(e):
        current_tab_index.value = e.control.selected_index
        apply_filter()

    sort_header = ft.Row(
        [
            ft.Text("並び順", weight="bold"),
            sort_button,
        ],
        spacing=5,
        vertical_alignment="center",
    )

    header_row = ft.Row(
        [
            sort_header,
        ],
        spacing=20,
        alignment="start",
    )

    tab = ft.Tabs(
        tabs=[
            ft.Tab(text="日報"),
            ft.Tab(text="引継")
        ],
        on_change=on_tab_change
    )

    search_data = load_results(0)
    total_pages = max(1, math.ceil(len(search_data) / items_per_page))

    pagination_row = ft.Row(page_controls().controls, alignment="center")

    build_page()

    return ft.Column(
        controls=[
            ft.Row([back_button], alignment="start"),
            title,
            ft.Divider(),
            tab,
            header_row,
            ft.Divider(),
            pagination_row,
            scrollable_area,
            ft.Divider(),
        ],
        spacing=10,
        expand=True
    )
