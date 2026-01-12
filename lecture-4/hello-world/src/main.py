import flet as ft
import requests
import sqlite3

# =========================
# データベース管理
# =========================
def init_db():
    """データベースとテーブルの初期化"""
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        area_code TEXT,
        date TEXT,
        weather_code TEXT,
        weather_text TEXT,
        min_temp TEXT,
        max_temp TEXT,
        PRIMARY KEY (area_code, date)
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS areas (
        code TEXT PRIMARY KEY,
        name TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def save_area_info(code, name):
    """エリア情報をDBに保存"""
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO areas (code, name) VALUES (?, ?)", (code, name))
    conn.commit()
    conn.close()

def save_weather(area, date, code, text, min_t, max_t):
    """天気予報データをDBに保存"""
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO weather
    (area_code, date, weather_code, weather_text, min_temp, max_temp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (area, date, code, text, min_t, max_t))
    conn.commit()
    conn.close()

def load_weather(area_code):
    """DBから特定のエリアの予報を取得（今日以降に限定）"""
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    # 過去のデータが溜まりすぎないよう、今日以降のデータを取得
    cur.execute("""
    SELECT date, weather_code, weather_text, min_temp, max_temp
    FROM weather
    WHERE area_code = ? AND date >= date('now', 'localtime')
    ORDER BY date ASC
    """, (area_code,))
    data = cur.fetchall()
    conn.close()
    return data

# =========================
# メインアプリケーション
# =========================
def main(page: ft.Page):
    page.title = "Weather Forecast Pro (DB Edition)"
    page.theme_mode = "dark"
    page.bgcolor = "#F0F2F5"
    page.padding = 0

    # 天気コード変換辞書
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
        """コードから絵文字・色・テキストを解決する"""
        main_code = str(code)
        if main_code in WEATHER_MAP:
            return WEATHER_MAP[main_code]
        # 前方一致でのフォールバック
        if main_code.startswith("1"): return "☀️", "#FFA000", text_fallback or "晴れ"
        if main_code.startswith("2"): return "☁️", "#90A4AE", text_fallback or "曇り"
        if main_code.startswith("3"): return "☔️", "#1E88E5", text_fallback or "雨"
        if main_code.startswith("4"): return "❄️", "#4FC3F7", text_fallback or "雪"
        return "❓", "#B0BEC5", text_fallback or "不明"

    def create_weather_row(date_str, emoji, icon_color, weather_text, min_t, max_t):
        """1日分の予報行のデザイン"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(date_str, size=16, color="#607D8B", weight="bold", width=70),
                    ft.Text(emoji, size=35),
                    ft.Container(
                        content=ft.Text(weather_text, size=14, weight="w700", color="#263238"),
                        expand=True,
                        padding=ft.padding.only(left=15)
                    ),
                    ft.Row(
                        [
                            ft.Text(f"{min_t}°", size=16, weight="bold", color="#1976D2"),
                            ft.Text("/", size=14, color="#CFD8DC"),
                            ft.Text(f"{max_t}°", size=16, weight="bold", color="#D32F2F"),
                        ],
                        alignment="end",
                    ),
                ],
                alignment="center",
            ),
            bgcolor="white",
            padding=20,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color="#15000000"),
        )

    def on_area_selected(e):
        area_code = e.control.data
        area_name = e.control.title.value
        selected_city_text.value = f"{area_name} の1週間予報"
        
        # UIリセットとローディング表示
        weather_cards.controls.clear()
        weather_cards.controls.append(ft.ProgressBar(width=400, color="blue"))
        page.update()

        save_area_info(area_code, area_name)
        
        try:
            raw_data = requests.get(f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json").json()
            merged = {}

            # --- 1. 週間予報からベースを作成 ---
            week_times = raw_data[1]["timeSeries"][0]["timeDefines"]
            week_codes = raw_data[1]["timeSeries"][0]["areas"][0]["weatherCodes"]
            week_min = raw_data[1]["timeSeries"][1]["areas"][0].get("tempsMin", [])
            week_max = raw_data[1]["timeSeries"][1]["areas"][0].get("tempsMax", [])

            for i in range(len(week_times)):
                d_iso = week_times[i][:10]
                w_code = week_codes[i]
                
                # ここで「週間予報」という文字の代わりに、コードから変換した名称を取得
                _, _, weather_name = get_weather_details(w_code)
                
                merged[d_iso] = {
                    "code": w_code, 
                    "text": weather_name, 
                    "min": week_min[i] if i < len(week_min) else "--",
                    "max": week_max[i] if i < len(week_max) else "--"
                }

            # --- 2. 短期予報で詳細を補完 ---
            short_times = raw_data[0]["timeSeries"][0]["timeDefines"]
            short_codes = raw_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"]
            short_weathers = raw_data[0]["timeSeries"][0]["areas"][0].get("weathers", [])
            short_temps = raw_data[0]["timeSeries"][2]["areas"][0].get("temps", []) if len(raw_data[0]["timeSeries"]) > 2 else []

            for i in range(len(short_times)):
                d_iso = short_times[i][:10]
                if d_iso not in merged: merged[d_iso] = {"min": "--", "max": "--"}
                
                merged[d_iso]["code"] = short_codes[i]
                # 短期予報にある詳細な説明文（例：「くもり　時々　雨」）があれば上書き
                if i < len(short_weathers): 
                    merged[d_iso]["text"] = short_weathers[i]
                
                if len(short_temps) > i*2 and short_temps[i*2]: merged[d_iso]["min"] = short_temps[i*2]
                if len(short_temps) > i*2+1 and short_temps[i*2+1]: merged[d_iso]["max"] = short_temps[i*2+1]

            # --- 3. DBへ格納 ---
            for d_iso, val in merged.items():
                save_weather(area_code, d_iso, val["code"], val["text"], val["min"], val["max"])
        
        except Exception as ex:
            print(f"Fetch Error: {ex}")

        # --- 4. DBからデータを読み込んで表示更新 ---
        weather_cards.controls.clear()
        db_rows = load_weather(area_code)
        
        if not db_rows:
            weather_cards.controls.append(ft.Text("データを取得できませんでした。", color="red"))
        else:
            for date, code, text, min_t, max_t in db_rows:
                # get_weather_details を通してアイコンと色を取得（textは保存された詳細文を使用）
                emoji, color, _ = get_weather_details(code)
                d_display = date[5:].replace("-", "/")
                weather_cards.controls.append(create_weather_row(d_display, emoji, color, text, min_t or "--", max_t or "--"))
        
        page.update()

    # --- UIレイアウト ---
    area_data = requests.get("http://www.jma.go.jp/bosai/common/const/area.json").json()
    sidebar_items = [
        ft.Container(
            content=ft.Text("地域を選択", size=12, weight="bold", color="#90A4AE"),
            padding=ft.padding.only(left=20, top=30, bottom=10),
        )
    ]

    for c_code, c_info in area_data["centers"].items():
        display_name = c_info["name"].replace("（山口県を除く）", "").replace("（山口県を含む）", "")
        children = []
        for o_code in c_info["children"]:
            if o_code in area_data["offices"]:
                children.append(
                    ft.ListTile(
                        title=ft.Text(area_data["offices"][o_code]["name"], size=14, color="#ECEFF1"),
                        data=o_code, on_click=on_area_selected,
                    )
                )
        if children:
            sidebar_items.append(
                ft.ExpansionTile(
                    title=ft.Text(display_name, size=15, weight="bold", color="white"),
                    controls=children,
                )
            )

    sidebar = ft.Container(content=ft.Column(sidebar_items, scroll="auto"), width=260, bgcolor="#1C2331")
    selected_city_text = ft.Text("地域を選択してください", size=24, weight="bold", color="#263238")
    weather_cards = ft.Column(spacing=15)
    main_content = ft.Container(
        content=ft.Column([selected_city_text, ft.Divider(height=10, color="transparent"), weather_cards], scroll="auto"),
        expand=True, padding=30,
    )

    header = ft.Container(
        content=ft.Text("☀️ 天気予報 Pro (SQLite版) ☀️", size=20, weight="bold", color="#263238"),
        padding=ft.padding.symmetric(vertical=15),
        bgcolor="white", alignment=ft.alignment.center,
        border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0")),
    )

    page.add(
        ft.Column(
            [header, ft.Row([sidebar, main_content], expand=True, spacing=0)],
            expand=True, spacing=0,
        )
    )

if __name__ == "__main__":
    init_db()
    ft.app(target=main)