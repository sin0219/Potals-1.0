import flet as ft 
import sqlite3
import asyncio
import os
import subprocess
import tempfile
import db
from urllib.parse import parse_qs, urlparse

def handover_detail_view(page: ft.Page):
    url_parts = urlparse(page.route)
    handover_id = int(url_parts.path.split("/")[-1])
    query_params = parse_qs(url_parts.query)
    return_to = query_params.get('from', ['/handover_list'])[0]

    # データ取得
    conn = sqlite3.connect("data/portal.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, detail, attachment_path, updated_at, updated_by, approved_by, origin
        FROM handovers
        WHERE id = ?
    """, (handover_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return ft.Text("データが見つかりません", color="red")

    title, detail, attachment_path, updated_at, updated_by, approved_by, origin_name = row
    attachment_name = os.path.basename(attachment_path) if attachment_path else ""
    approver_list = [name.strip() for name in approved_by.split(",") if name.strip()]
    approver_count = len(approver_list)

    # origin の色取得
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT color FROM origins WHERE name = ?", (origin_name,))
    origin_color_row = cursor.fetchone()
    conn.close()
    origin_color = origin_color_row[0] if origin_color_row else "#CCCCCC"

    # 発信元アイコン
    origin_icon = ft.Container(
        content=ft.Text(origin_name or "不明", size=12, color="white"),
        width=80,
        height=30,
        bgcolor=origin_color,
        border_radius=15,
        alignment=ft.alignment.center,
        tooltip=origin_name or "不明",
    )

    # 印刷処理
    def print_handover(e):
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
                tmp.write(f"【引継内容】\n")
                tmp.write(f"タイトル: {title}\n")
                tmp.write(f"発信元: {origin_name}\n")
                tmp.write(f"詳細:\n{detail}\n")
                tmp.write(f"添付ファイル: {attachment_name or 'なし'}\n")
                tmp.write(f"更新日付: {updated_at}\n")
                tmp.write(f"更新者: {updated_by}\n")
                tmp.write(f"認証者数: {approver_count}名\n")
                tmp_path = tmp.name

            subprocess.Popen(['notepad', '/p', tmp_path], shell=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"印刷エラー: {ex}", color="red"))
            page.snack_bar.open = True
            page.update()

    # 共通UI
    user_id = ft.TextField(label="ID", width=250)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=250)
    error_text = ft.Text("", color="red")

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("認証（管理者）"),
        content=ft.Column([user_id, password, error_text], tight=True),
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def close_dialog(e):
        page.close(dlg_modal)

    async def on_delete_confirm(e):
        uid = user_id.value.strip()
        pwd = password.value.strip()
        if not uid or not pwd:
            error_text.value = "IDとパスワードを入力してください"
            page.update()
            return

        conn = sqlite3.connect("data/portal.db")
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM accounts WHERE user_id=? AND password=?", (uid, pwd))
        res = cursor.fetchone()
        conn.close()

        if res and res[0] == 1:
            conn = sqlite3.connect("data/portal.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM handovers WHERE id = ?", (handover_id,))
            conn.commit()
            conn.close()

            page.close(dlg_modal)
            await asyncio.sleep(0.1)
            page.go(return_to)
        else:
            error_text.value = "認証に失敗しました"
            page.update()

    async def on_approve_confirm(e):
        uid = user_id.value.strip()
        pwd = password.value.strip()
        if not uid or not pwd:
            error_text.value = "IDとパスワードを入力してください"
            page.update()
            return

        conn = sqlite3.connect("data/portal.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts WHERE user_id=? AND password=?", (uid, pwd))
        res = cursor.fetchone()

        if res:
            approver_name = res[0]

            cursor.execute("SELECT approved_by FROM handovers WHERE id=?", (handover_id,))
            approved_by_raw = cursor.fetchone()[0] or ""
            current_approvers = [n.strip() for n in approved_by_raw.split(",") if n.strip()]

            if approver_name in current_approvers:
                error_text.value = "すでに認証済みです"
                conn.close()
                page.update()
                return

            current_approvers.append(approver_name)
            new_approved_by = ", ".join(current_approvers)

            cursor.execute("""
                UPDATE handovers
                SET approved_by = ?
                WHERE id = ?
            """, (new_approved_by, handover_id))
            conn.commit()
            conn.close()

            page.close(dlg_modal)
            await asyncio.sleep(0.1)
            page.go(return_to)
        else:
            conn.close()
            error_text.value = "認証に失敗しました"
            page.update()

    async def on_edit_confirm(e):
        uid = user_id.value.strip()
        pwd = password.value.strip()
        if not uid or not pwd:
            error_text.value = "IDとパスワードを入力してください"
            page.update()
            return

        conn = sqlite3.connect("data/portal.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, is_admin FROM accounts WHERE user_id=? AND password=?", (uid, pwd))
        res = cursor.fetchone()
        conn.close()

        if res:
            user_name, is_admin = res
            if user_name == updated_by or is_admin == 1:
                page.close(dlg_modal)
                await asyncio.sleep(0.1)
                page.go(f"/handover_edit/{handover_id}")
            else:
                error_text.value = "更新者または管理者のみ編集可能です"
                page.update()
        else:
            error_text.value = "認証に失敗しました"
            page.update()

    def open_delete_dialog(e):
        user_id.value = ""
        password.value = ""
        error_text.value = ""
        dlg_modal.title = ft.Text("削除認証（管理者）")
        dlg_modal.actions = [
            ft.TextButton("削除", on_click=on_delete_confirm),
            ft.TextButton("キャンセル", on_click=close_dialog),
        ]
        page.dialog = dlg_modal
        page.open(dlg_modal)

    def open_approve_dialog(e):
        user_id.value = ""
        password.value = ""
        error_text.value = ""
        dlg_modal.title = ft.Text("認証")
        dlg_modal.actions = [
            ft.TextButton("認証する", on_click=on_approve_confirm),
            ft.TextButton("キャンセル", on_click=close_dialog),
        ]
        page.dialog = dlg_modal
        page.open(dlg_modal)

    def open_edit_dialog(e):
        user_id.value = ""
        password.value = ""
        error_text.value = ""
        dlg_modal.title = ft.Text("編集認証（更新者または管理者）")
        dlg_modal.actions = [
            ft.TextButton("編集する", on_click=on_edit_confirm),
            ft.TextButton("キャンセル", on_click=close_dialog),
        ]
        page.dialog = dlg_modal
        page.open(dlg_modal)

    def open_attachment(e):
        if attachment_path and os.path.exists(attachment_path):
            try:
                subprocess.Popen(['start', '', attachment_path], shell=True)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"ファイルを開けません: {ex}", color="red"))
                page.snack_bar.open = True
                page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("ファイルが存在しません", color="red"))
            page.snack_bar.open = True
            page.update()

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("引継 詳細", size=24, weight="bold"),
                ft.Divider(),
                ft.Text(f"タイトル: {title}", size=18),
                origin_icon,
                ft.Text(f"詳細:\n{detail}", size=16),
                ft.Row([
                    ft.Text("添付ファイル: ", size=16),
                    ft.TextButton(text=attachment_name, on_click=open_attachment) if attachment_path else ft.Text("なし", size=16)
                ]),
                ft.Text(f"更新日付: {updated_at}", size=16),
                ft.Text(f"更新者: {updated_by}", size=16),
                ft.Text(f"認証者数: {approver_count}名", size=16),
                ft.Divider(),
                ft.Row(
                    [
                        ft.TextButton(text="戻る", icon="arrow_back", on_click=lambda e: page.go(return_to)),
                        ft.ElevatedButton(text="認証する", icon="check", on_click=open_approve_dialog),
                        ft.IconButton(icon="edit", tooltip="編集", on_click=open_edit_dialog),
                        ft.IconButton(icon="delete", tooltip="削除", icon_color="gray", on_click=open_delete_dialog),
                        ft.IconButton(icon="print", tooltip="印刷", on_click=print_handover),
                    ],
                    spacing=20,
                )
            ],
            spacing=15,
            scroll="auto",
            expand=True,
        ),
        padding=20,
    )
