import flet as ft

def admin_settings_view(page: ft.Page) -> ft.View:
    return ft.View(
        route="/admin_settings",
        controls=[
            ft.Text("システム設定", size=28, weight="bold"),
            ft.Divider(),
            ft.Text("ここに会社名・UIカラー設定などが表示されます（テスト）"),
            ft.ElevatedButton("戻る", on_click=lambda e: page.go("/admin_top"))
        ],
        padding=30
    )
