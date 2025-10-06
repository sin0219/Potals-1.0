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

def show_mypage_login_dialog(page: ft.Page):
    """マイページ用ログインダイアログ"""
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
                "SELECT name FROM accounts WHERE user_id=? AND password=?",
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

        if res:
            # ログイン成功 - ユーザー名を保存
            # 修正前: page.client_storage.set("mypage_user_name", res[0])
            # 修正後:
            page.session.set("mypage_user_name", res[0])
            page.close(dlg_modal)
            await asyncio.sleep(0.1)
            page.go("/mypage")
        else:
            error_text.value = "認証に失敗しました"
            page.update()

    def close_dialog(e):
        page.close(dlg_modal)

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("マイページログイン"),
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
    page.padding = 20
    page.bgcolor = "#f8fafc"

    # ヘッダー部分（ロゴ画像使用）
    header = ft.Container(
        content=ft.Column([
            # メインロゴ画像
            ft.Container(
                content=ft.Image(
                    src="/logo/portal_logo.png",
                    width=600,
                    height=200,
                    fit=ft.ImageFit.CONTAIN
                ),
                padding=20
            ),
            
            ft.Container(height=10),
            
            # サブタイトル
            ft.Text(
                "✨ あなたの業務をスマートに管理",
                size=18,
                text_align="center",
                color="#64748b",
                weight="w400"
            ),
        ], horizontal_alignment="center"),
        padding=ft.padding.symmetric(vertical=40),
        alignment=ft.alignment.center
    )

    # 検索バー
    search_input = ft.TextField(
        label="何をお探しですか？",
        width=400,
        border_radius=25,
        filled=True,
        bgcolor="white",
        border_color="#e2e8f0"
    )
    search_button = ft.ElevatedButton(
        "検索",
        width=100,
        style=ft.ButtonStyle(
            bgcolor="#3b82f6",
            color="white",
            shape=ft.RoundedRectangleBorder(radius=20)
        )
    )

    def on_search_click(e):
        keyword = search_input.value.strip()
        if keyword:
            page.go(f"/search?keyword={keyword}")

    search_button.on_click = on_search_click

    search_container = ft.Container(
        content=ft.Row(
            controls=[search_input, search_button],
            alignment="center",
            spacing=15
        ),
        padding=20,
        alignment=ft.alignment.center
    )

    # メニューカード作成関数
    def create_menu_card(icon, title, subtitle, color, on_click):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=48, color=color),
                    ft.Text(title, size=20, weight="bold", color="#1e293b"),
                    ft.Text(subtitle, size=14, color="#64748b", text_align="center"),
                ], spacing=15, horizontal_alignment="center"),
                padding=30,
                width=280,
                height=180,
                on_click=on_click,
                ink=True
            ),
            elevation=4,
            color="white",
            surface_tint_color=color
        )

    # メインメニューカード
    main_menu = ft.Row([
        create_menu_card(
            "assignment", "日報管理", "日々の業務報告を\n効率的に管理", "#10b981",
            lambda e: page.go("/daily_top")
        ),
        create_menu_card(
            "swap_horiz", "引継管理", "重要な情報を\n確実に引き継ぎ", "#f59e0b",
            lambda e: page.go("/handover_list")
        ),
        create_menu_card(
            "person", "マイページ", "個人設定と\nプロフィール管理", "#8b5cf6",
            lambda e: show_mypage_login_dialog(page)
        ),
    ], alignment="center", spacing=20, wrap=True)

    # クイックアクション
    quick_actions = ft.Container(
        content=ft.Column([
            ft.Text("クイックアクション", size=20, weight="bold", color="#1e293b", text_align="center"),
            ft.Row([
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Icon("add_circle_outline", size=24, color="#3b82f6"),
                            ft.Text("新規日報", size=16, color="#1e293b")
                        ], spacing=10),
                        padding=15,
                        on_click=lambda e: page.go("/daily/create"),
                        ink=True
                    ),
                    elevation=2,
                    color="white"
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Icon("note_add", size=24, color="#10b981"),
                            ft.Text("新規引継", size=16, color="#1e293b")
                        ], spacing=10),
                        padding=15,
                        on_click=lambda e: page.go("/handover_create"),
                        ink=True
                    ),
                    elevation=2,
                    color="white"
                ),
            ], alignment="center", spacing=15)
        ], spacing=15, horizontal_alignment="center"),
        padding=ft.padding.only(top=40),
        alignment=ft.alignment.center
    )

    # アカウント管理セクション
    account_section = ft.Container(
        content=ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("アカウント管理", size=18, weight="bold", color="#1e293b"),
                    ft.Row([
                        ft.TextButton(
                            "新規アカウント作成",
                            icon="person_add",
                            on_click=lambda e: page.go("/account_create"),
                            style=ft.ButtonStyle(color="#3b82f6")
                        ),
                        ft.TextButton(
                            "アカウント変更",
                            icon="edit",
                            on_click=lambda e: page.go("/account_check"),
                            style=ft.ButtonStyle(color="#3b82f6")
                        ),
                    ], alignment="center", spacing=20)
                ], spacing=15, horizontal_alignment="center"),
                padding=25,
            ),
            elevation=2,
            color="white"
        ),
        padding=ft.padding.only(top=30),
        alignment=ft.alignment.center
    )

    # 管理者メニュー
    admin_section = ft.Container(
        content=ft.TextButton(
            "管理者メニュー",
            icon="admin_panel_settings",
            on_click=lambda e: show_admin_login_dialog(page),
            style=ft.ButtonStyle(
                color="#ef4444",
                bgcolor="#fef2f2",
                shape=ft.RoundedRectangleBorder(radius=15)
            )
        ),
        padding=ft.padding.only(top=20),
        alignment=ft.alignment.center
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                header,
                search_container,
                main_menu,
                quick_actions,
                account_section,
                admin_section
            ],
            horizontal_alignment="center",
            spacing=0,
            scroll="auto"
        ),
        bgcolor="#f8fafc",
        expand=True
    )