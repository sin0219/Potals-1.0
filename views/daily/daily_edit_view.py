import flet as ft
import sqlite3
import os
import shutil
import datetime
import asyncio
from urllib.parse import parse_qs, urlparse

UPLOAD_DIR = "assets/daily_files"

# DBパス
DB_PATH = os.path.join("data", "portal.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def daily_edit_view(page: ft.Page):
    # URLパラメータからIDを取得
    url_parts = urlparse(page.route)
    query_params = parse_qs(url_parts.query)
    
    if 'id' not in query_params:
        return ft.Text("IDが指定されていません", color="red")
    
    daily_id = int(query_params['id'][0])

    # 現在のデータを取得
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT time, detail, attachment_path, updated_at, updated_by
        FROM daily
        WHERE rowid = ?
    """, (daily_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return ft.Text("データが見つかりません", color="red")

    current_time, current_detail, current_attachment_path, current_updated_at, current_updated_by = row
    
    # 日付部分を抽出
    current_date_str = current_updated_at.split()[0] if current_updated_at else datetime.date.today().strftime("%Y-%m-%d")
    current_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d").date()

    # 選択日付の管理
    selected_date_text = ft.Text(current_date.strftime("%Y-%m-%d"), size=18)
    selected_date_value = {"value": current_date}

    # DatePicker
    date_picker = ft.DatePicker(
        first_date=datetime.date(2024, 1, 1),
        last_date=datetime.date(2026, 12, 31),
        on_change=lambda e: on_date_change()
    )
    page.overlay.append(date_picker)

    def on_date_select(e):
        page.open(date_picker)

    def on_date_change():
        if date_picker.value:
            selected_date_value["value"] = date_picker.value
            selected_date_text.value = date_picker.value.strftime("%Y-%m-%d")
            page.update()

    # 時間入力（現在の値を設定）
    time_field = ft.TextField(
        label="時間（例：0930 → 09:30）",
        width=150,
        value=current_time or "",
        input_filter=ft.InputFilter(allow=True, regex_string=r"\d{0,4}", replacement_string=""),
    )

    time_picker = ft.TimePicker(
        confirm_text="OK",
        cancel_text="キャンセル",
        on_change=lambda e: update_time_from_picker()
    )
    page.overlay.append(time_picker)

    def update_time_from_picker():
        if time_picker.value:
            time_field.value = time_picker.value.strftime("%H:%M")
            page.update()

    time_row = ft.Row([
        time_field,
        ft.IconButton(icon="access_time", tooltip="時間を選択", on_click=lambda e: page.open(time_picker))
    ])

    # 詳細入力（現在の値を設定）
    detail_field = ft.TextField(
        label="詳細", 
        multiline=True, 
        min_lines=5, 
        expand=True, 
        value=current_detail or ""
    )

    # 添付ファイル
    selected_file_path = ft.Text(value="", visible=False)
    attachment_text = ft.Text(
        value=os.path.basename(current_attachment_path) if current_attachment_path else "", 
        expand=True
    )

    def remove_file(e):
        selected_file_path.value = ""
        attachment_text.value = ""
        remove_button.visible = False
        page.update()

    remove_button = ft.IconButton(
        icon="close", 
        tooltip="添付を削除", 
        visible=bool(current_attachment_path), 
        on_click=remove_file
    )

    def pick_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_file_path.value = e.files[0].path
            attachment_text.value = os.path.basename(selected_file_path.value)
            remove_button.visible = True
            page.update()

    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)

    upload_row = ft.Row([
        ft.IconButton(icon="attachment", tooltip="ファイルを添付", on_click=lambda e: file_picker.pick_files()),
        attachment_text,
        remove_button
    ], spacing=10)

    error_text = ft.Text(color="red")

    def update_data(updated_by):
        time_val = time_field.value.strip()
        detail_val = detail_field.value.strip()
        selected_date = selected_date_value["value"]

        # 時間フォーマット変換
        if len(time_val) == 4:
            time_val = f"{time_val[:2]}:{time_val[2:]}"  # 0930 → 09:30

        if not time_val:
            error_text.value = "時間を入力してください"
            page.update()
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        attachment_db_path = current_attachment_path

        # 新しいファイルが選択された場合
        if selected_file_path.value:
            filename = f"{now.replace(':', '').replace(' ', '_')}_{os.path.basename(selected_file_path.value)}"
            dst_path = os.path.join(UPLOAD_DIR, filename)
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            shutil.copyfile(selected_file_path.value, dst_path)
            attachment_db_path = dst_path

        # 更新日時を選択した日付+時間で設定
        updated_at_str = selected_date.strftime("%Y-%m-%d") + " " + time_val

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE daily
            SET updated_at = ?, time = ?, updated_by = ?, detail = ?, attachment_path = ?
            WHERE rowid = ?
        """, (updated_at_str, time_val, updated_by, detail_val, attachment_db_path, daily_id))
        conn.commit()
        conn.close()
        page.go("/daily")

    def show_login_dialog(e):
        user_id = ft.TextField(label="ID", width=250)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=250)
        login_error = ft.Text("", color="red")

        async def on_login(ev):
            uid = user_id.value.strip()
            pwd = password.value.strip()

            if not uid or not pwd:
                login_error.value = "IDとパスワードを入力してください"
                page.update()
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, is_admin FROM accounts WHERE user_id=? AND password=?", (uid, pwd))
            res = cursor.fetchone()
            conn.close()

            if res:
                name, is_admin = res
                # 更新者または管理者であるか確認
                if name == current_updated_by or is_admin == 1:
                    page.close(login_dialog)
                    await asyncio.sleep(0.1)
                    update_data(name)
                else:
                    login_error.value = "編集権限がありません（更新者または管理者のみ）"
                    page.update()
            else:
                login_error.value = "認証に失敗しました"
                page.update()

        def close_dialog(ev):
            page.close(login_dialog)

        login_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("編集認証"),
            content=ft.Column([user_id, password, login_error], tight=True),
            actions=[
                ft.TextButton("保存", on_click=on_login),
                ft.TextButton("キャンセル", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = login_dialog
        page.open(login_dialog)

    save_button = ft.ElevatedButton("保存", on_click=show_login_dialog)
    cancel_button = ft.TextButton("キャンセル", on_click=lambda e: page.go("/daily"))

    return ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("日報 編集", size=24, weight="bold"),
            ft.Row([
                ft.Text("日付: ", size=18),
                selected_date_text,
                ft.IconButton(icon="calendar_today", tooltip="日付を選択", on_click=on_date_select)
            ], spacing=10),
            time_row,
            detail_field,
            upload_row,
            error_text,
            ft.Row([save_button, cancel_button], spacing=20),
        ], spacing=20)
    )