import flet as ft
import db

def admin_accounts_view(page: ft.Page) -> ft.View:
    def load_accounts():
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, user_id, password, is_admin, created_at FROM accounts ORDER BY id")
        accounts = cursor.fetchall()
        conn.close()
        return accounts

    def refresh_table():
        for i, control in enumerate(view.controls):
            if isinstance(control, ft.DataTable):
                view.controls[i] = create_table(load_accounts())
                break
        page.update()

    def delete_account(account_id):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        conn.commit()
        conn.close()
        refresh_table()

    def update_admin_status(account_id, is_admin):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET is_admin=? WHERE id=?", (1 if is_admin else 0, account_id))
        conn.commit()
        conn.close()
        # 状態はすぐに反映するのでrefresh_tableはしない

    def show_confirm_dialog(e, account_id):
        def on_confirm(e):
            page.close(confirm_dialog)
            page.update()
            delete_account(account_id)

        def on_cancel(e):
            page.close(confirm_dialog)
            page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("確認"),
            content=ft.Text("このアカウントを削除しますか？"),
            actions=[
                ft.TextButton("はい", on_click=on_confirm),
                ft.TextButton("キャンセル", on_click=on_cancel)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = confirm_dialog
        page.open(confirm_dialog)

    def create_table(rows):
        def on_toggle_change(e, account_id):
            update_admin_status(account_id, e.control.value)
        
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("名前")),
                ft.DataColumn(ft.Text("ユーザーID")),
                ft.DataColumn(ft.Text("パスワード")),
                ft.DataColumn(ft.Text("権限")),
                ft.DataColumn(ft.Text("作成日")),
                ft.DataColumn(ft.Text("操作")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row[0]))),        # id
                        ft.DataCell(ft.Text(row[1])),              # name
                        ft.DataCell(ft.Text(row[2])),              # user_id
                        ft.DataCell(ft.Text(row[3])),              # password
                        ft.DataCell(
                            ft.Switch(
                                value=(row[4] == 1),
                                label="管理者",
                                on_change=lambda e, account_id=row[0]: on_toggle_change(e, account_id)
                            )
                        ),  # is_admin をトグルスイッチに
                        ft.DataCell(ft.Text(row[5])),              # created_at
                        ft.DataCell(
                            ft.IconButton(
                                icon="delete",
                                icon_color="red",
                                tooltip="削除",
                                on_click=lambda e, id=row[0]: show_confirm_dialog(e, id)
                            )
                        ),
                    ]
                )
                for row in rows
            ]
        )

    accounts = load_accounts()
    table = create_table(accounts)

    view = ft.View(
        route="/admin_accounts",
        controls=[
            ft.Text("アカウント一覧", size=28, weight="bold"),
            ft.Divider(),
            table,
            ft.Divider(),
            ft.ElevatedButton("戻る", on_click=lambda e: page.go("/admin_top")),
        ],
        padding=30,
        scroll="auto"
    )
    return view
