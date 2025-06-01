import flet as ft
import sqlite3
import os
import shutil
import datetime
import asyncio

UPLOAD_DIR = "assets/handover_files"

def handover_edit_view(page: ft.Page):
    handover_id = int(page.route.split("/")[-1])
    conn = sqlite3.connect("data/portal.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, detail, attachment_path, origin
        FROM handovers WHERE id = ?
    """, (handover_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return ft.Text("データが見つかりません", color="red")

    current_title, current_detail, current_attachment_path, current_origin = row

    title_input = ft.TextField(label="タイトル", expand=True, value=current_title)
    detail_input = ft.TextField(label="詳細", multiline=True, min_lines=5, expand=True, value=current_detail)
    selected_file_path = ft.Text(value="", visible=False)

    # --- 発信元プルダウン ---
    origin_dropdown = ft.Dropdown(label="発信元", width=300, value=current_origin)
    def load_origins():
        conn = sqlite3.connect("data/portal.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM origins ORDER BY name")
        origins = cursor.fetchall()
        conn.close()
        origin_dropdown.options = [ft.dropdown.Option(name) for (name,) in origins]
    load_origins()
    # -----------------------

    attachment_text = ft.Text(value=os.path.basename(current_attachment_path) if current_attachment_path else "", expand=True)

    def remove_file(e):
        selected_file_path.value = ""
        attachment_text.value = ""
        remove_button.visible = False
        page.update()

    remove_button = ft.IconButton(icon="remove", tooltip="添付を削除", visible=bool(current_attachment_path), on_click=remove_file)

    def pick_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_file_path.value = e.files[0].path
            attachment_text.value = os.path.basename(selected_file_path.value)
            remove_button.visible = True
            page.update()

    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)

    upload_row = ft.Row(
        [
            ft.IconButton(icon="attachment", tooltip="ファイルを添付", on_click=lambda e: file_picker.pick_files()),
            attachment_text,
            remove_button,
        ],
        alignment="start",
        spacing=5,
    )

    error_text = ft.Text(color="red")

    def update_data(updated_by):
        title = title_input.value.strip()
        detail = detail_input.value.strip()
        origin_name = origin_dropdown.value

        if not title:
            error_text.value = "タイトルは必須です"
            page.update()
            return
        if not origin_name:
            error_text.value = "発信元を選択してください"
            page.update()
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        attachment_db_path = current_attachment_path

        if selected_file_path.value:
            filename = f"{now.replace(':', '').replace(' ', '_')}_{os.path.basename(selected_file_path.value)}"
            dst_path = os.path.join(UPLOAD_DIR, filename)
            shutil.copyfile(selected_file_path.value, dst_path)
            attachment_db_path = dst_path

        conn = sqlite3.connect("data/portal.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE handovers
            SET title = ?, detail = ?, updated_at = ?, updated_by = ?, attachment_path = ?, origin = ?
            WHERE id = ?
        """, (title, detail, now, updated_by, attachment_db_path, origin_name, handover_id))
        conn.commit()
        conn.close()
        page.go("/handover_list")

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

            conn = sqlite3.connect("data/portal.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name, is_admin FROM accounts WHERE user_id=? AND password=?", (uid, pwd))
            res = cursor.fetchone()
            conn.close()

            if res:
                name, is_admin = res
                # 更新者または管理者であるか確認
                cursor = sqlite3.connect("data/portal.db").cursor()
                cursor.execute("SELECT updated_by FROM handovers WHERE id = ?", (handover_id,))
                original_updater = cursor.fetchone()[0]
                if name == original_updater or is_admin == 1:
                    page.close(login_dialog)
                    await asyncio.sleep(0.1)
                    update_data(name)
                else:
                    login_error.value = "編集権限がありません"
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
    cancel_button = ft.TextButton("キャンセル", on_click=lambda e: page.go("/handover_list"))

    return ft.Column(
        [
            ft.Text("引継 編集", size=24, weight="bold"),
            title_input,
            origin_dropdown,
            detail_input,
            upload_row,
            error_text,
            ft.Row([save_button, cancel_button], spacing=10),
        ],
        spacing=20,
    )
