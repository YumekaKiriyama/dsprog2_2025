import flet as ft
import math

# ボタンクラス
class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__(text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK


class ScientificButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = ft.Colors.DEEP_PURPLE_300
        self.color = ft.Colors.WHITE

# 電卓本体
class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=24)
        self.width = 420
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20

        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),

                # --- 科学計算ボタン ---
                ft.Row(
                    controls=[
                        ScientificButton("sin", self.button_clicked),
                        ScientificButton("cos", self.button_clicked),
                        ScientificButton("tan", self.button_clicked),
                        ScientificButton("log", self.button_clicked),
                        ScientificButton("ln", self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ScientificButton("√", self.button_clicked),
                        ScientificButton("x²", self.button_clicked),
                        ScientificButton("xʸ", self.button_clicked),
                        ScientificButton("π", self.button_clicked),
                        ScientificButton("e", self.button_clicked),
                        ScientificButton("1/x", self.button_clicked),
                    ]
                ),

                ft.Row(
                    controls=[
                        ExtraActionButton("AC", self.button_clicked),
                        ExtraActionButton("+/-", self.button_clicked),
                        ExtraActionButton("%", self.button_clicked),
                        ActionButton("/", self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton("7", self.button_clicked),
                        DigitButton("8", self.button_clicked),
                        DigitButton("9", self.button_clicked),
                        ActionButton("*", self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton("4", self.button_clicked),
                        DigitButton("5", self.button_clicked),
                        DigitButton("6", self.button_clicked),
                        ActionButton("-", self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton("1", self.button_clicked),
                        DigitButton("2", self.button_clicked),
                        DigitButton("3", self.button_clicked),
                        ActionButton("+", self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton("0", self.button_clicked, expand=2),
                        DigitButton(".", self.button_clicked),
                        ActionButton("=", self.button_clicked),
                    ]
                ),
            ]
        )

    # ボタン処理
    def button_clicked(self, e):
        data = e.control.data

        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        elif data.isdigit() or data == ".":
            if self.result.value == "0" or self.new_operand:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value += data

        elif data in ("+", "-", "*", "/", "xʸ"):
            self.result.value = self.calculate(
                self.operand1, float(self.result.value), self.operator
            )
            self.operator = data
            self.operand1 = (
                0 if self.result.value == "Error" else float(self.result.value)
            )
            self.new_operand = True

        elif data == "=":
            self.result.value = self.calculate(
                self.operand1, float(self.result.value), self.operator
            )
            self.reset()

        elif data == "%":
            self.result.value = self.format_number(float(self.result.value) / 100)
            self.reset()

        elif data == "+/-":
            self.result.value = str(-float(self.result.value))

        # --- 定数 ---
        elif data == "π":
            self.result.value = self.format_number(math.pi)
            self.new_operand = True

        elif data == "e":
            self.result.value = self.format_number(math.e)
            self.new_operand = True

        # --- 単項科学計算 ---
        elif data in ("sin", "cos", "tan", "log", "ln", "√", "x²", "1/x"):
            try:
                v = float(self.result.value)

                if data == "sin":
                    self.result.value = self.format_number(
                        math.sin(math.radians(v))
                    )
                elif data == "cos":
                    self.result.value = self.format_number(
                        math.cos(math.radians(v))
                    )
                elif data == "tan":
                    self.result.value = self.format_number(
                        math.tan(math.radians(v))
                    )
                elif data == "log":
                    self.result.value = self.format_number(math.log10(v))
                elif data == "ln":
                    self.result.value = self.format_number(math.log(v))
                elif data == "√":
                    self.result.value = self.format_number(math.sqrt(v))
                elif data == "x²":
                    self.result.value = self.format_number(v ** 2)
                elif data == "1/x":
                    self.result.value = self.format_number(1 / v)

                self.reset()

            except:
                self.result.value = "Error"

        self.update()

    
    # 計算処理
    def calculate(self, operand1, operand2, operator):
        try:
            if operator == "+":
                return self.format_number(operand1 + operand2)
            elif operator == "-":
                return self.format_number(operand1 - operand2)
            elif operator == "*":
                return self.format_number(operand1 * operand2)
            elif operator == "/":
                return "Error" if operand2 == 0 else self.format_number(
                    operand1 / operand2
                )
            elif operator == "xʸ":
                return self.format_number(operand1 ** operand2)
        except:
            return "Error"

    def format_number(self, num):
        return int(num) if num % 1 == 0 else num

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


# エントリーポイント
def main(page: ft.Page):
    page.title = "Scientific Calculator"
    page.add(CalculatorApp())


ft.app(main)
