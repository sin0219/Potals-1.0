import flet as ft
import datetime
import sqlite3
import os

# DBパス
DB_PATH = os.path.join("data", "portal.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def fetch_daily_items_by_date(date_str):
    conn = get_connection()
    cursor = conn.cursor()
    like_pattern = date_str + "%"
    cursor.execute("""
        SELECT rowid, time, detail, approved_by, updated_by FROM daily
        WHERE updated_at LIKE ?
        ORDER BY time ASC
    """, (like_pattern,))
    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        rowid, time, detail, approved_by, updated_by = row
        approved_by_list = approved_by.split(",") if approved_by else []
        items.append({
            "rowid": rowid,
            "time": time,
            "content": detail,
            "updated_by": updated_by if updated_by else "未設定",
            "approved_by_count": len([name for name in approved_by_list if name.strip()])
        })
    return items

def daily_top_view(page: ft.Page):
    now = datetime.datetime.now()
    initial_date = now.date() if now.hour >= 11 else now.date() - datetime.timedelta(days=1)

    selected_date_ref = ft.Ref[ft.Text]()
    current_date = {"value": initial_date}
    items_list_column = ft.Column(spacing=10)

    date_picker = ft.DatePicker(
        first_date=datetime.datetime(2024, 1, 1),
        last_date=datetime.datetime(2026, 12, 31),
        on_change=lambda e: on_date_change(e)
    )
    page.overlay.append(date_picker)

    def load_items_for_date(date_obj):
        date_str = date_obj.strftime("%Y-%m-%d")
        current_date["value"] = date_obj
        if selected_date_ref.current:
            selected_date_ref.current.value = date_str
        items_list_column.controls.clear()
        items = fetch_daily_items_by_date(date_str)
        for item in items:
            items_list_column.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{item['time']} - {item['updated_by']} - {item['content']}"),
                    trailing=ft.Text(f"{item['approved_by_count']}名認証", size=12, color="gray"),
                    on_click=on_item_click,
                    data=item
                )
            )
        page.update()

    def on_date_select(e):
        page.open(date_picker)

    def on_date_change(e):
        if date_picker.value:
            load_items_for_date(date_picker.value)

    def on_create_new(e):
        page.go(f"/daily/create?date={current_date['value'].strftime('%Y-%m-%d')}")

    def on_item_click(e):
        item = e.control.data
        rowid = item["rowid"]
        page.go(f"/daily/detail?id={rowid}")

    def on_prev_day(e):
        new_date = current_date["value"] - datetime.timedelta(days=1)
        load_items_for_date(new_date)

    def on_next_day(e):
        new_date = current_date["value"] + datetime.timedelta(days=1)
        load_items_for_date(new_date)

    # 戻るボタンは、一番外側のColumnの最後で定義
    back_button = ft.ElevatedButton("戻る", on_click=lambda e: page.go("/"))

    # スクロール可能な領域のContainerからheightを削除し、Columnにexpand=Trueを付与
    # これにより、このColumnが利用可能な残りのスペースを全て占有する
    scrollable_area = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("報告一覧", size=18, weight="bold"),
                items_list_column
            ],
            spacing=10,
            scroll="auto",
            expand=True # Columnが利用可能なスペースを拡大
        ),
        # height=500, # この行を削除
        expand=True # Containerも利用可能なスペースを拡大
    )

    # 一番外側のColumnのalignmentを調整し、expand=Trueを付与
    content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("日報一覧", size=22, weight="bold"),
                    ],
                    alignment="start",
                ),
                ft.Row(
                    controls=[
                        ft.Row([
                            ft.IconButton(
                                icon="chevron_left",
                                icon_color="blue",
                                tooltip="前日へ",
                                on_click=on_prev_day
                            ),
                            ft.Text("日付: ", size=20),
                            ft.Text(initial_date.strftime("%Y-%m-%d"), size=20, ref=selected_date_ref),
                            ft.IconButton(
                                icon="calendar_today",
                                icon_color="blue",
                                tooltip="日付選択",
                                on_click=on_date_select
                            ),
                            ft.IconButton(
                                icon="chevron_right",
                                icon_color="blue",
                                tooltip="翌日へ",
                                on_click=on_next_day
                            ),
                            ft.Text("（～AM11:00遷移）", size=14, color="gray"),
                        ], alignment="center", spacing=10),
                        ft.IconButton(
                            icon="add",
                            icon_color="white",
                            bgcolor="blue",
                            tooltip="新規作成",
                            on_click=on_create_new
                        ),
                    ],
                    alignment="spaceBetween"
                ),
                ft.Divider(),
                scrollable_area, # expand=Trueがここで重要
                ft.Divider(),
                ft.Row([back_button], alignment="start"), # 戻るボタンを一番外側のColumnの最後に配置
            ],
            spacing=20,
            expand=True, # Columnが利用可能なスペースを拡大
            # vertical_alignment="spaceBetween" # この行を削除。戻るボタンが下部に固定されるように調整
        ),
        padding=20,
        expand=True # Containerも利用可能なスペースを拡大
    )

    load_items_for_date(initial_date)

    return content