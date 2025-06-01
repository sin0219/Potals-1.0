import flet as ft

def admin_top_view(page: ft.Page) -> ft.View:
    return ft.View(
        route="/admin_top",
        controls=[
            ft.Text("管理者メニュー", size=36, weight="bold", text_align="center"),
            ft.Divider(),

            ft.Column(
                controls=[
                    ft.ElevatedButton("アカウント管理", width=300, on_click=lambda e: page.go("/admin_accounts")),
                    ft.ElevatedButton("システム設定", width=300, on_click=lambda e: page.go("/admin_settings")),
                    ft.ElevatedButton("ログ閲覧", width=300, on_click=lambda e: page.go("/admin_logs")),
                    ft.ElevatedButton("発信元マスタ管理", width=300, on_click=lambda e: page.go("/admin_origins")),
                    ft.ElevatedButton("マスタ管理", width=300, on_click=lambda e: page.go("/admin_master")),
                ],
                alignment="center",
                horizontal_alignment="center",
                spacing=10
            ),

            ft.Divider(),

            ft.Container(
                content=ft.TextButton("トップに戻る", on_click=lambda e: page.go("/")),
                alignment=ft.alignment.center,
                padding=10
            )
        ],
        horizontal_alignment="center",
        vertical_alignment="start",
        padding=30,
        scroll="auto",
        appbar=ft.AppBar(
            title=ft.Text("STRPORTAL - 管理者"),
            center_title=True,
        )
    )
