import flet as ft
import datetime
import urllib.parse
import os  # ← これが必要

from views.top_view import top_view
from views.account.account_create_view import account_create_view
from views.account.account_check_view import account_check_view
from views.account.account_edit_view import account_edit_view
from views.admin.admin_top_view import admin_top_view
from views.admin.admin_accounts_view import admin_accounts_view
from views.admin.admin_settings_view import admin_settings_view
from views.admin.admin_logs_view import admin_logs_view
from views.admin.admin_master_view import admin_master_view
from views.admin.admin_origins_view import admin_origins_view
from views.handover.handover_list_view import handover_list_view
from views.handover.handover_detail_view import handover_detail_view
from views.handover.handover_create_view import handover_create_view
from views.handover.handover_edit_view import handover_edit_view
from views.daily.daily_top_view import daily_top_view
from views.daily.daily_create_view import daily_create_view
from views.daily.daily_detail_view import daily_detail_view
from views.daily.daily_edit_view import daily_edit_view
from views.search.search_result_view import search_result_view
from views.search.search_handover_view import search_handover_view
from views.search.search_daily_view import search_daily_view
from views.mypage.mypage_view import mypage_view
import db

def main(page: ft.Page):
    db.init_db()

    def route_change(route):
        page.views.clear()

        if page.route == "/":
            page.views.append(ft.View("/", [top_view(page)]))
        elif page.route == "/account_create":
            page.views.append(ft.View("/account_create", [account_create_view(page)]))
        elif page.route == "/account_check":
            page.views.append(ft.View("/account_check", [account_check_view(page)]))
        elif page.route == "/account_edit":
            page.views.append(ft.View("/account_edit", [account_edit_view(page)]))
        elif page.route == "/admin_top":
            page.views.append(admin_top_view(page))
        elif page.route == "/admin_accounts":
            page.views.append(admin_accounts_view(page))
        elif page.route == "/admin_settings":
            page.views.append(admin_settings_view(page))
        elif page.route == "/admin_logs":
            page.views.append(admin_logs_view(page))
        elif page.route == "/admin_master":
            page.views.append(admin_master_view(page))
        elif page.route == "/admin_origins":
            page.views.append(ft.View("/admin_origins", [admin_origins_view(page)]))
        elif page.route == "/handover_list":
            page.views.append(ft.View("/handover_list", [handover_list_view(page)]))
        elif page.route.startswith("/handover_detail"):
            page.views.append(ft.View(page.route, [handover_detail_view(page)]))
        elif page.route == "/handover_create":
            page.views.append(ft.View("/handover_create", [handover_create_view(page)]))
        elif page.route.startswith("/handover_edit"):
            page.views.append(ft.View(page.route, [handover_edit_view(page)]))
        elif page.route == "/daily" or page.route == "/daily_top":
            page.views.append(ft.View(page.route, [daily_top_view(page)]))
        elif page.route.startswith("/daily/create"):
            parsed = urllib.parse.urlparse(page.route)
            params = urllib.parse.parse_qs(parsed.query)
            date_str = params.get("date", [datetime.date.today().strftime("%Y-%m-%d")])[0]
            try:
                selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                selected_date = datetime.date.today()
            page.views.append(ft.View(page.route, [daily_create_view(page, selected_date)]))
        elif page.route.startswith("/daily/detail"):
            page.views.append(ft.View(page.route, [daily_detail_view(page)]))
        elif page.route.startswith("/daily/edit"):
            page.views.append(ft.View(page.route, [daily_edit_view(page)]))
        elif page.route.startswith("/search_daily"):
            page.views.append(ft.View(page.route, [search_daily_view(page)]))
        elif page.route.startswith("/search_handover"):
            page.views.append(ft.View(page.route, [search_handover_view(page)]))
        elif page.route == "/mypage":  # ← この3行を追加
            page.views.append(ft.View("/mypage", [mypage_view(page)]))   
        elif page.route.startswith("/search"):
            page.views.append(ft.View(page.route, [search_result_view(page)]))

        page.update()

    page.on_route_change = route_change
    page.go(page.route)

# Renderが渡してくるPORTを使う（無ければ8080）
port = int(os.environ.get("PORT", 8080))

# 重要：host="0.0.0.0" にして外部からアクセス可能にする
ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")