# views/account_create_view.py
import flet as ft
import db

def account_create_view(page: ft.Page):
    name = ft.TextField(label="ユーザー名", width=300)
    user_id = ft.TextField(label="ID", width=300)
    password = ft.TextField(label="パスワード", password=True, can_reveal_password=True, width=300)
    message = ft.Text()

    def submit(e):
        if not name.value or not user_id.value or not password.value:
            message.value = "すべての項目を入力してください。"
            message.color = "red"
            page.update()
            return

        conn = db.get_connection()
        cursor = conn.cursor()

        # IDの重複チェック
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ?", (user_id.value,))
        if cursor.fetchone()[0] > 0:
            message.value = "このIDはすでに使用されています。"
            message.color = "red"
            conn.close()
            page.update()
            return

        try:
            cursor.execute(
                "INSERT INTO accounts (name, user_id, password) VALUES (?, ?, ?)",
                (name.value, user_id.value, password.value)
            )
            conn.commit()
            message.value = "アカウントを作成しました！"
            message.color = "green"
            name.value = user_id.value = password.value = ""
        except Exception as ex:
            message.value = f"エラー：{str(ex)}"
            message.color = "red"
        finally:
            conn.close()
            page.update()

    return ft.Column(
        [
            ft.Text("新規アカウント作成", size=24, weight="bold"),
            name,
            user_id,
            password,
            ft.ElevatedButton("作成", on_click=submit),
            message,
            ft.TextButton("← 戻る", on_click=lambda e: page.go("/"))
        ],
        spacing=20
    )
