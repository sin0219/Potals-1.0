import flet as ft
import db
import sqlite3
import math

def handover_list_view(page: ft.Page):
    page.title = "引継一覧"
    page.padding = 30

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM origins")
    origin_list = [row[0] for row in cursor.fetchall()]
    conn.close()

    # フィルター状態
    sort_descending = ft.Ref[bool]()
    sort_descending.value = True
    selected_origin = ft.Ref[str]()
    selected_origin.value = "すべて"

    def fetch_filtered_data():
        conn = db.get_connection()
        cursor = conn.cursor()
        query = """
            SELECT h.id, h.updated_at, h.title, h.updated_by, h.approved_by, h.origin, o.color
            FROM handovers h
            LEFT JOIN origins o ON h.origin = o.name
        """
        conditions = []
        params = []

        if selected_origin.value != "すべて":
            conditions.append("h.origin = ?")
            params.append(selected_origin.value)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        order = "DESC" if sort_descending.value else "ASC"
        query += f" ORDER BY h.updated_at {order}"

        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data

    # ページング設定
    items_per_page = 10
    current_page = ft.Ref[int]()
    current_page.value = 1

    data_list_column = ft.Column(spacing=10)
    scrollable_area = ft.Container(
        content=ft.Column(controls=[data_list_column], scroll="auto", expand=True),
        height=600,
        expand=True
    )

    # 並び替えのアイコンボタン
    sort_button = ft.IconButton(
        icon="arrow_downward",
        tooltip="更新日付で並び替え",
        on_click=lambda e: toggle_sort()
    )

    # 発信元のドロップダウン
    origin_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option("すべて")] + [ft.dropdown.Option(name) for name in origin_list],
        value="すべて",
        on_change=lambda e: apply_filter(),
        width=120, # ドロップダウンの幅を固定
    )

    def toggle_sort():
        sort_descending.value = not sort_descending.value
        sort_button.icon = "arrow_downward" if sort_descending.value else "arrow_upward"
        apply_filter()

    def apply_filter():
        nonlocal handover_data, total_pages
        selected_origin.value = origin_dropdown.value
        current_page.value = 1
        handover_data = fetch_filtered_data()
        total_pages = max(1, math.ceil(len(handover_data) / items_per_page))
        build_page()
        pagination_row.controls = page_controls().controls
        page.update()

    # データ描画
    def build_page():
        start = (current_page.value - 1) * items_per_page
        end = start + items_per_page
        page_data = handover_data[start:end]

        rows = []
        for row in page_data:
            hid, updated_at, title, updated_by, approved_by, origin_name, origin_color = row
            approvers = [a.strip() for a in approved_by.split(",") if a.strip()]
            approver_count = len(approvers)

            origin_label = ft.Container(
                content=ft.Text(origin_name or "不明", size=10, color="white"),
                width=60,
                height=24,
                alignment=ft.alignment.center,
                border_radius=12,
                bgcolor=origin_color or "#CCCCCC",
                tooltip=origin_name or "不明",
            )

            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(updated_at, width=120),
                            # ここにContainerを追加して発信元列の開始位置を調整
                            ft.Container(width=50), # 調整用の空白。この値を調整してください
                            origin_label,
                            # ここにContainerを追加してタイトル列の開始位置を調整
                            ft.Container(width=100), # 調整用の空白。この値を調整してください
                            ft.Text(title, expand=1),
                            ft.Text(updated_by, width=100),
                            ft.Text(f"{approver_count}名", width=100),
                        ],
                        spacing=0, # 各要素間のspacingを0にして、Containerで幅を調整する
                        vertical_alignment="center",
                    ),
                    on_click=lambda e, handover_id=hid: page.go(f"/handover_detail/{handover_id}"),
                    ink=True,
                    border_radius=5,
                    padding=10,
                    bgcolor="lightgrey",
                    margin=ft.margin.only(bottom=5),
                )
            )

        data_list_column.controls = rows
        page.update()

    # ページネーション
    def page_controls():
        return ft.Row(
            controls=[
                ft.IconButton(icon="first_page", tooltip="先頭", on_click=lambda e: change_page(1), disabled=current_page.value == 1),
                ft.IconButton(icon="chevron_left", tooltip="前へ", on_click=lambda e: change_page(current_page.value - 1), disabled=current_page.value == 1),
                ft.Text(f"{current_page.value} / {total_pages}", size=14, weight="bold"),
                ft.IconButton(icon="chevron_right", tooltip="次へ", on_click=lambda e: change_page(current_page.value + 1), disabled=current_page.value == total_pages),
                ft.IconButton(icon="last_page", tooltip="最後", on_click=lambda e: change_page(total_pages), disabled=current_page.value == total_pages),
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

    # 初期データ取得
    handover_data = fetch_filtered_data()
    total_pages = max(1, math.ceil(len(handover_data) / items_per_page))

    # タイトル
    new_button = ft.IconButton(
        icon="add",
        icon_color="white",
        bgcolor="blue",
        tooltip="新規作成",
        on_click=lambda e: page.go("/handover_create"),
    )

    top_row = ft.Row(
        [ft.Text("引継一覧", size=24, weight="bold"), ft.Container(expand=1), new_button],
        alignment="center",
        spacing=10,
    )

    # 「更新日付」ラベル＋並び替えボタンの横並び
    updated_at_header = ft.Row(
        [
            ft.Text("  更新日付", weight="bold", width=80),#空白は配置調整
            sort_button,
        ],
        spacing=0,
        vertical_alignment="center",
        width=120,
    )

    # 「発信元」ラベル＋ドロップダウンの横並び
    origin_header = ft.Row(
        [
            ft.Text("発信元", weight="bold"),
            origin_dropdown,
        ],
        spacing=5,
        vertical_alignment="center",
        width=180,
    )

    # ヘッダー行（ラベルとボタン・プルダウンを横並びで）
    header_row = ft.Row(
        [
            updated_at_header,
            origin_header,
            ft.Text("タイトル", weight="bold", expand=1),
            ft.Text("      更新者", weight="bold", width=100),#空白は配置調整
            ft.Text("認証者数", weight="bold", width=100),
            ft.Container(width=10), # 調整用の空白。この値を調整してください
        ],
        spacing=20, # データ行のspacingと合わせる
        alignment="start",
    )

    # 戻るボタン
    back_button = ft.ElevatedButton("戻る", on_click=lambda e: page.go("/"))

    # ページネーション行（位置変更）
    pagination_row = ft.Row(page_controls().controls, alignment="center")

    # 初期描画
    build_page()

    return ft.Column(
        [
            top_row,
            pagination_row,
            header_row,
            ft.Divider(),
            scrollable_area,
            ft.Divider(),
            back_button,
        ],
        spacing=20,
        expand=True,
    )