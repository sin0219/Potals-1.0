import flet as ft
from db import get_connection

def admin_origins_view(page: ft.Page):
    page.title = "発信元マスタ管理"
    page.scroll = "auto"

    origin_input = ft.TextField(label="発信元名", expand=True)
    color_input = ft.TextField(label="色", value="#000000", width=150, read_only=True)
    
    # 色プレビュー用のコンテナ
    color_preview = ft.Container(
        width=40,
        height=40,
        bgcolor="#000000",
        border_radius=5,
        margin=ft.margin.only(left=5, right=5)
    )
    
    error_text = ft.Text(color="red")
    origins_column = ft.Column(spacing=10)

    # 固定カラーパレット
    color_palette = [
        "#000000", "#FF0000", "#00FF00", "#0000FF", "#FFFF00",
        "#FF00FF", "#00FFFF", "#808080", "#800000", "#008000",
        "#000080", "#808000", "#800080", "#008080", "#C0C0C0",
        "#FFA500", "#A52A2A", "#7FFF00", "#DC143C", "#00CED1"
    ]

    # 選択中のフィールド保持用
    selected_color_field = None
    selected_preview = None

    def make_color_button(color_code):
        def on_color_click(e):
            if selected_color_field:
                selected_color_field.value = color_code
                if selected_preview:
                    selected_preview.bgcolor = color_code
                page.update()
            page.close(color_dialog)
            
        return ft.Container(
            width=30,
            height=30,
            bgcolor=color_code,
            border_radius=5,
            on_click=on_color_click,
            ink=True,  # クリック効果を追加
        )

    def show_color_dialog(e, field, preview):
        nonlocal selected_color_field, selected_preview
        selected_color_field = field
        selected_preview = preview

        # 色ボタンを行に分けて配置
        buttons_per_row = 5
        rows = []
        for i in range(0, len(color_palette), buttons_per_row):
            row_colors = color_palette[i:i+buttons_per_row]
            row = ft.Row(
                [make_color_button(color) for color in row_colors],
                spacing=10
            )
            rows.append(row)

        def close_dialog(e):
            page.close(color_dialog)

        # サンプルコードを参考に、ダイアログを作成
        global color_dialog
        color_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("色を選択"),
            content=ft.Column(rows, tight=True),
            actions=[
                ft.TextButton("キャンセル", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.dialog = color_dialog
        page.open(color_dialog)  # openを使う（closeとセット）

    def load_origins():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, color FROM origins ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        origins_column.controls.clear()

        for origin_id, name, color in rows:
            name_field = ft.TextField(value=name, expand=True)
            color_field = ft.TextField(value=color or "#000000", width=120, read_only=True)
            
            # 色プレビュー用のコンテナ
            preview = ft.Container(
                width=40,
                height=40,
                bgcolor=color or "#000000",
                border_radius=5,
                margin=ft.margin.only(left=5, right=5)
            )
            
            # それぞれの行に個別の関数を作成
            def make_color_click_handler(cf, pv):
                return lambda e: show_color_dialog(e, cf, pv)
                
            def make_update_click_handler(oid, nf, cf):
                return lambda e: update_origin(oid, nf.value, cf.value)
                
            def make_delete_click_handler(oid):
                return lambda e: delete_origin(oid)
            
            color_btn = ft.IconButton(
                icon="palette", 
                tooltip="色選択", 
                on_click=make_color_click_handler(color_field, preview)
            )
            
            update_btn = ft.IconButton(
                icon="edit", 
                tooltip="更新", 
                on_click=make_update_click_handler(origin_id, name_field, color_field)
            )
            
            delete_btn = ft.IconButton(
                icon="delete", 
                tooltip="削除", 
                on_click=make_delete_click_handler(origin_id)
            )

            row = ft.Row([
                name_field, 
                color_field, 
                preview,  # 色プレビュー追加
                color_btn, 
                update_btn, 
                delete_btn
            ], alignment="center", vertical_alignment="center")  # 縦方向の揃えを追加
            
            origins_column.controls.append(row)

        page.update()

    def add_origin(e):
        name = origin_input.value.strip()
        color = color_input.value.strip()
        if not name:
            error_text.value = "名前を入力してください"
            page.update()
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO origins (name, color) VALUES (?, ?)", (name, color))
        conn.commit()
        conn.close()

        origin_input.value = ""
        color_input.value = "#000000"
        color_preview.bgcolor = "#000000"  # プレビューの色もリセット
        error_text.value = ""
        load_origins()

    def update_origin(origin_id, new_name, new_color):
        new_name = new_name.strip()
        new_color = new_color.strip()
        if not new_name:
            error_text.value = "名前を空にはできません"
            page.update()
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE origins SET name=?, color=? WHERE id=?", (new_name, new_color, origin_id))
        conn.commit()
        conn.close()
        load_origins()

    def delete_origin(origin_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM origins WHERE id=?", (origin_id,))
        conn.commit()
        conn.close()
        load_origins()

    back_button = ft.TextButton("戻る", on_click=lambda e: page.go("/admin_top"))
    
    # 新規追加用の色選択ボタン用関数
    def show_color_picker(e):
        show_color_dialog(e, color_input, color_preview)

    # 色選択ボタン
    color_picker_btn = ft.IconButton(
        icon="palette", 
        on_click=show_color_picker
    )

    load_origins()

    # 入力フォームのレイアウト
    input_row = ft.Row([
        origin_input,
        color_input,
        color_preview,  # プレビュー追加
        color_picker_btn,
        ft.ElevatedButton("追加", on_click=add_origin)
    ], spacing=10, alignment="center", vertical_alignment="center")  # 縦方向の揃えを追加

    return ft.Column([
        ft.Text("発信元マスタ管理", size=24, weight="bold"),
        input_row,
        error_text,
        ft.Divider(),
        origins_column,
        ft.Divider(),
        back_button,
    ], spacing=20, expand=True, scroll="auto")