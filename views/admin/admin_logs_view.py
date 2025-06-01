import flet as ft

def admin_logs_view(page: ft.Page) -> ft.View:
    return ft.View(
        route="/admin_logs",
        controls=[
            ft.Text("操作ログ閲覧", size=28, weight="bold"),
            ft.Divider(),
            ft.Text("ここに操作ログ一覧が表示されます（テスト）"),
            ft.ElevatedButton("戻る", on_click=lambda e: page.go("/admin_top"))
        ],
        padding=30
    )
