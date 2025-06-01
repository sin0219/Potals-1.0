import flet as ft
import sqlite3
import asyncio

def show_admin_login_dialog(page: ft.Page):
    user_id = ft.TextField(label="ID", width=250)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=250)
    error_text = ft.Text("", color="red")

    async def on_login(e):
        uid = user_id.value.strip()
        pwd = password.value.strip()
        if not uid or not pwd:
            error_text.value = "IDとパスワードを入力してください"
            page.update()
            return

        conn = None
        try:
            conn = sqlite3.connect("data/portal.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_admin FROM accounts WHERE user_id=? AND password=?",
                (uid, pwd)
            )
            res = cursor.fetchone()
        except Exception as ex:
            error_text.value = f"DBエラー: {ex}"
            page.update()
            return
        finally:
            if conn:
                conn.close()

        if res and res[0] == 1:
            page.close(dlg_modal)
            page.update()
            await asyncio.sleep(0.1)
            page.go("/admin_top")
        else:
            error_text.value = "認証に失敗しました"
            page.update()

    def close_dialog(e):
        page.close(dlg_modal)

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("管理者ログイン"),
        content=ft.Column([user_id, password, error_text], tight=True),
        actions=[
            ft.TextButton("ログイン", on_click=on_login),
            ft.TextButton("キャンセル", on_click=close_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.dialog = dlg_modal
    page.open(dlg_modal)


def top_view(page: ft.Page):
    page.title = "PORTALs"
    page.scroll = "auto"
    page.padding = 30

    title = ft.Text("PORTALs", size=36, weight="bold", text_align="center")

    # 🔍 検索バーのUI定義
    search_input = ft.TextField(label="検索ワード", width=300)
    search_button = ft.ElevatedButton("検索", width=100)

    def on_search_click(e):
        keyword = search_input.value.strip()
        if keyword:
            page.go(f"/search?keyword={keyword}")

    search_button.on_click = on_search_click

    search_bar = ft.Row(
        controls=[search_input, search_button],
        alignment="center"
    )

    menu_buttons = ft.Column(
        [
            ft.ElevatedButton("日報", width=300, on_click=lambda e: page.go("/daily_top")),
            ft.ElevatedButton("引継", width=300, on_click=lambda e: page.go("/handover_list")),
            ft.ElevatedButton("マイページ", width=300),
        ],
        alignment="center",
        horizontal_alignment="center",
        spacing=10,
    )

    account_buttons = ft.Row(
        [
            ft.TextButton("新規アカウント作成", on_click=lambda e: page.go("/account_create")),
            ft.TextButton("アカウント変更", on_click=lambda e: page.go("/account_check")),
        ],
        alignment="center"
    )

    admin_button = ft.Container(
        ft.TextButton("管理者メニュー", on_click=lambda e: show_admin_login_dialog(page)),
        alignment=ft.alignment.center,
        padding=10
    )

    return ft.Column(
        controls=[
            title,
            search_bar,  # ← タイトル下に検索バー追加
            ft.Divider(),
            menu_buttons,
            ft.Divider(),
            account_buttons,
            ft.Divider(),
            admin_button
        ],
        horizontal_alignment="center",
        alignment="start",
        spacing=30
    )
