# views/account_edit_view.py
import flet as ft
import db

def account_edit_view(page: ft.Page):
    account_id = page.client_storage.get("edit_account_id")

    if not account_id:
        page.go("/")
        return

    name = ft.TextField(label="ユーザー名", width=300)
    user_id = ft.TextField(label="ID", width=300)
    password = ft.TextField(label="パスワード", password=True, can_reveal_password=True, width=300)
    message = ft.Text()

    # アカウント情報を事前に読み込み
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, user_id, password FROM accounts WHERE id = ?", (account_id,))
    result = cursor.fetchone()

    if result:
        name.value, user_id.value, password.value = result

    def update_account(e):
        if not name.value or not user_id.value or not password.value:
            message.value = "すべての項目を入力してください。"
            message.color = "red"
            page.update()
            return

        # IDが他のアカウントと重複していないか確認
        cursor.execute(
            "SELECT COUNT(*) FROM accounts WHERE user_id = ? AND id != ?",
            (user_id.value, account_id)
        )
        if cursor.fetchone()[0] > 0:
            message.value = "このIDはすでに使用されています。"
            message.color = "red"
            page.update()
            return

        try:
            cursor.execute("""
                UPDATE accounts SET name = ?, user_id = ?, password = ? WHERE id = ?
            """, (name.value, user_id.value, password.value, account_id))
            conn.commit()
            message.value = "更新しました！"
            message.color = "green"
        except Exception as ex:
            message.value = f"エラー：{str(ex)}"
            message.color = "red"
        finally:
            conn.close()
            page.update()

    return ft.Column(
        [
            ft.Text("アカウント情報の変更", size=24, weight="bold"),
            name,
            user_id,
            password,
            ft.ElevatedButton("更新", on_click=update_account),
            message,
            ft.TextButton("← 戻る", on_click=lambda e: page.go("/"))
        ],
        spacing=20
    )
