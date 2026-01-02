import flet as ft
import requests

def main(page: ft.Page):
    page.title = "Weather Forecast Pro"
    page.theme_mode = "dark"
    page.bgcolor = "#F0F2F5"
    page.padding = 0

    # =========================
    # 天気コード → (絵文字, 色, テキスト) 変換辞書
    # =========================
    # アイコン名を絵文字に変更しました
    WEATHER_MAP = {
        "100": ("☀️", "#FFA000", "晴れ"),
        "101": ("🌤️", "#FFA000", "晴れ時々曇り"),
        "110": ("🌤️", "#FFA000", "晴れ後時々曇り"),
        "200": ("☁️", "#90A4AE", "曇り"),
        "201": ("🌤️", "#90A4AE", "曇り時々晴れ"),
        "210": ("🌥️", "#90A4AE", "曇り後晴れ"),
        "300": ("☔️", "#1E88E5", "雨"),
        "301": ("🌦️", "#1E88E5", "雨時々晴れ"),
        "311": ("🌧️", "#1E88E5", "雨時々曇り"),
        "400": ("❄️", "#4FC3F7", "雪"),
    }

    def get_weather_details(code, text_fallback=""):
        main_code = str(code)
        if main_code in WEATHER_MAP:
            return WEATHER_MAP[main_code]
        
        # 辞書にない場合のフォールバック判定（絵文字対応）
        if main_code.startswith("1"): return "☀️", "#FFA000", text_fallback or "晴れ"
        if main_code.startswith("2"): return "☁️", "#90A4AE", text_fallback or "曇り"
        if main_code.startswith("3"): return "☔️", "#1E88E5", text_fallback or "雨"
        if main_code.startswith("4"): return "❄️", "#4FC3F7", text_fallback or "雪"
        return "❓", "#B0BEC5", text_fallback or "不明"

    # =========================
    # API取得
    # =========================
    def get_areas():
        return requests.get("http://www.jma.go.jp/bosai/common/const/area.json").json()

    def get_weather_data(area_code):
        return requests.get(f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json").json()

    # =========================
    # カード作成関数（ft.Icon を ft.Text に変更）
    # =========================
    def create_weather_card(date_str, emoji, icon_color, weather_text, min_t, max_t):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(date_str, size=14, color="#607D8B", weight="bold"),
                    # アイコンの代わりに絵文字テキストを表示
                    ft.Text(emoji, size=45), 
                    ft.Text(
                        weather_text,
                        size=12,
                        weight="w700",
                        color="#263238",
                        text_align="center",
                        height=35,
                    ),
                    ft.Row(
                        [
                            ft.Text(f"{min_t}°", size=14, weight="bold", color="#1976D2"),
                            ft.Text("/", size=14, color="#CFD8DC"),
                            ft.Text(f"{max_t}°", size=14, weight="bold", color="#D32F2F"),
                        ],
                        alignment="center",
                    ),
                ],
                alignment="center",
                horizontal_alignment="center",
                spacing=5,
            ),
            width=140,
            height=200,
            padding=15,
            bgcolor="white",
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color="#20000000"),
        )

    # =========================
    # 地域選択イベント (ロジック変更なし)
    # =========================
    def on_area_selected(e):
        area_code = e.control.data
        raw_data = get_weather_data(area_code)
        
        weather_cards.controls.clear()
        selected_city_text.value = f"{e.control.title.value} の1週間予報"

        short_times = raw_data[0]["timeSeries"][0]["timeDefines"]
        short_codes = raw_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"]
        short_weathers = raw_data[0]["timeSeries"][0]["areas"][0].get("weathers", [])
        
        short_temps = []
        if len(raw_data[0]["timeSeries"]) > 2:
            short_temps = raw_data[0]["timeSeries"][2]["areas"][0].get("temps", [])

        week_times = raw_data[1]["timeSeries"][0]["timeDefines"]
        week_codes = raw_data[1]["timeSeries"][0]["areas"][0]["weatherCodes"]
        week_temps_min = raw_data[1]["timeSeries"][1]["areas"][0].get("tempsMin", [])
        week_temps_max = raw_data[1]["timeSeries"][1]["areas"][0].get("tempsMax", [])

        processed_dates = set()

        for i in range(len(short_times)):
            d_iso = short_times[i][:10]
            d_display = d_iso[5:].replace("-", "/")
            emoji, color, txt = get_weather_details(
                short_codes[i], 
                short_weathers[i] if i < len(short_weathers) else ""
            )
            t_min = short_temps[i*2] if len(short_temps) > i*2 else "--"
            t_max = short_temps[i*2+1] if len(short_temps) > i*2+1 else "--"
            
            weather_cards.controls.append(create_weather_card(d_display, emoji, color, txt, t_min, t_max))
            processed_dates.add(d_iso)

        for i in range(len(week_times)):
            d_iso = week_times[i][:10]
            if d_iso in processed_dates:
                continue
            
            d_display = d_iso[5:].replace("-", "/")
            emoji, color, txt = get_weather_details(week_codes[i])
            t_min = week_temps_min[i] if i < len(week_temps_min) else "--"
            t_max = week_temps_max[i] if i < len(week_temps_max) else "--"
            
            weather_cards.controls.append(create_weather_card(d_display, emoji, color, txt, t_min, t_max))

        page.update()

    # =========================
    # サイドバー・レイアウト (変更なし)
    # =========================
    area_data = get_areas()
    centers = area_data["centers"]
    offices = area_data["offices"]

    sidebar_items = [
        ft.Container(
            content=ft.Text("地域を選択", size=12, weight="bold", color="#90A4AE"),
            padding=ft.padding.only(left=20, top=30, bottom=10),
        )
    ]

    for c_code, c_info in centers.items():
        display_name = c_info["name"].replace("（山口県を除く）", "").replace("（山口県を含む）", "")
        children = []
        for o_code in c_info["children"]:
            if o_code in offices:
                children.append(
                    ft.ListTile(
                        title=ft.Text(offices[o_code]["name"], size=14, color="#ECEFF1"),
                        data=o_code,
                        on_click=on_area_selected,
                    )
                )
        if children:
            sidebar_items.append(
                ft.ExpansionTile(
                    title=ft.Text(display_name, size=15, weight="bold", color="white"),
                    controls=children,
                )
            )

    sidebar = ft.Container(
        content=ft.Column(sidebar_items, scroll="auto"),
        width=260,
        bgcolor="#1C2331",
    )

    selected_city_text = ft.Text("地域を選択してください", size=24, weight="bold", color="#263238")
    weather_cards = ft.Row(wrap=True, spacing=15, scroll="auto")

    main_content = ft.Container(
        content=ft.Column(
            [
                selected_city_text,
                ft.Divider(height=10, color="transparent"),
                weather_cards,
            ],
            scroll="auto",
        ),
        expand=True,
        padding=30,
    )

    header = ft.Container(
        content=ft.Text("☀️天気予報☀️", size=20, weight="bold", color="#263238"),
        padding=ft.padding.symmetric(vertical=15),
        bgcolor="white",
        alignment=ft.alignment.center,
        border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0")),
    )

    page.add(
        ft.Column(
            [
                header,
                ft.Row([sidebar, main_content], expand=True, spacing=0),
            ],
            expand=True,
            spacing=0,
        )
    )

ft.app(target=main)