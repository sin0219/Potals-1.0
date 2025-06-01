import flet as ft

def admin_master_view(page: ft.Page) -> ft.View:
    return ft.View(
        route="/admin_master",
        controls=[
            ft.Text("マスタ管理", size=28, weight="bold"),
            ft.Divider(),
            ft.Text("ここにCSVインポート・エクスポート機能などが追加されます（テスト）"),
            ft.ElevatedButton("戻る", on_click=lambda e: page.go("/admin_top"))
        ],
        padding=30
    )
