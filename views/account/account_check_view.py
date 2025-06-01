# views/account_check_view.py
import flet as ft
import db

def account_check_view(page: ft.Page):
    user_id = ft.TextField(label="ID", width=300)
    password = ft.TextField(label="パスワード", password=True, can_reveal_password=True, width=300)
    message = ft.Text()

    def check_account(e):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM accounts WHERE user_id = ? AND password = ?",
            (user_id.value, password.value)
        )
        account = cursor.fetchone()
        conn.close()

        if account:
            page.client_storage.set("edit_account_id", account[0])  # IDを保存しておく
            page.go("/account_edit")
        else:
            message.value = "IDまたはパスワードが間違っています。"
            message.color = "red"
            page.update()

    return ft.Column(
        [
            ft.Text("アカウント認証（変更用）", size=24, weight="bold"),
            user_id,
            password,
            ft.ElevatedButton("次へ", on_click=check_account),
            message,
            ft.TextButton("← 戻る", on_click=lambda e: page.go("/"))
        ],
        spacing=20
    )
