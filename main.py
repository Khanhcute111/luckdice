"""Luck Dice Offline - giao diện Kivy (2 tab: Người chơi / Admin)."""
import os
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import DEFAULT_FONT, LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import core
from core import GameError, money

KV = """
#:import dp kivy.metrics.dp

<Btn@Button>:
    size_hint_y: None
    height: dp(44)
    background_normal: ''
    background_color: 0.16, 0.45, 0.85, 1

<Field@TextInput>:
    size_hint_y: None
    height: dp(44)
    multiline: False
    write_tab: False
    padding: dp(10), dp(12)

<Heading@Label>:
    size_hint_y: None
    height: dp(30)
    bold: True
    color: 0.55, 0.8, 1, 1

<Note@Label>:
    size_hint_y: None
    height: self.texture_size[1] + dp(8)
    text_size: self.width, None
    markup: True
    valign: 'top'

<Root>:
    canvas.before:
        Color:
            rgba: 0.04, 0.1, 0.18, 1
        Rectangle:
            pos: self.pos
            size: self.size
    TabbedPanel:
        do_default_tab: False
        tab_width: self.width / 2
        tab_height: dp(44)
        TabbedPanelItem:
            text: 'Người chơi'
            PlayerTab:
                id: player
        TabbedPanelItem:
            text: 'Admin'
            AdminTab:
                id: admin

<PlayerTab>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(8)
    Label:
        text: root.balance_text
        font_size: '26sp'
        bold: True
        size_hint_y: None
        height: dp(48)
        color: 1, 0.84, 0.2, 1
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)
        Spinner:
            id: game
            on_text: root.on_game(self.text)
        Spinner:
            id: choice
    Field:
        id: amount
        text: '10000'
        input_filter: 'int'
        hint_text: 'Số xu cược'
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(6)
        Btn:
            text: '1K'
            on_release: root.set_amount(1000)
        Btn:
            text: '10K'
            on_release: root.set_amount(10000)
        Btn:
            text: '50K'
            on_release: root.set_amount(50000)
        Btn:
            text: 'Tất cả'
            on_release: root.set_amount(-1)
    Btn:
        id: play_btn
        text: 'ĐỔ XÚC XẮC'
        height: dp(54)
        bold: True
        background_color: 0.1, 0.65, 0.35, 1
        on_release: root.play()
    Label:
        text: root.result_text
        markup: True
        font_size: '17sp'
        size_hint_y: None
        height: dp(100)
        text_size: self.width, None
        halign: 'center'
        valign: 'middle'
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)
        Field:
            id: gift
            hint_text: 'Nhập gifcode'
        Btn:
            text: 'Đổi code'
            size_hint_x: 0.4
            on_release: root.redeem()
    Heading:
        text: 'Lịch sử gần đây'
    ScrollView:
        Note:
            text: root.history_text

<AdminLock>:
    orientation: 'vertical'
    padding: dp(24)
    spacing: dp(10)
    Widget:
    Heading:
        text: 'Khu vực Admin - nhập PIN (mặc định 1234)'
    Field:
        id: pin
        password: True
        hint_text: 'PIN'
        on_text_validate: root.unlock()
    Btn:
        text: 'Mở khóa'
        on_release: root.unlock()
    Note:
        text: root.message
        halign: 'center'
    Widget:

<AdminPanel>:
    ScrollView:
        GridLayout:
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(8)
            padding: dp(10)
            Heading:
                text: 'Thống kê'
            Note:
                text: root.stats_text
            Heading:
                text: 'Ví xu'
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                spacing: dp(8)
                Field:
                    id: bal
                    input_filter: 'int'
                    hint_text: 'Số xu mới'
                Btn:
                    text: 'Đặt xu'
                    size_hint_x: 0.4
                    on_release: root.set_balance()
            Heading:
                text: 'Quản lý gifcode'
            Note:
                text: root.gifts_text
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                spacing: dp(6)
                Field:
                    id: g_code
                    hint_text: 'Mã'
                Field:
                    id: g_amount
                    input_filter: 'int'
                    hint_text: 'Xu'
                Field:
                    id: g_uses
                    input_filter: 'int'
                    hint_text: 'Số lần'
                    text: '1'
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                spacing: dp(8)
                Btn:
                    text: 'Tạo / cập nhật'
                    on_release: root.create_gift()
                Btn:
                    text: 'Xóa code'
                    background_color: 0.75, 0.3, 0.25, 1
                    on_release: root.delete_gift()
            Heading:
                text: 'Dữ liệu'
            Btn:
                text: 'Xuất lịch sử ra CSV'
                on_release: root.export_csv()
            Btn:
                text: 'Reset ví + lịch sử'
                background_color: 0.75, 0.3, 0.25, 1
                on_release: root.reset()
            Heading:
                text: 'Bảo mật'
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                spacing: dp(8)
                Field:
                    id: new_pin
                    password: True
                    hint_text: 'PIN mới (>= 4 ký tự)'
                Btn:
                    text: 'Đổi PIN'
                    size_hint_x: 0.4
                    on_release: root.change_pin()
            Btn:
                text: 'Khóa lại'
                on_release: root.tab.show_lock()
            Note:
                text: root.status
"""


def confirm(title, message, on_yes):
    box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
    box.add_widget(Label(text=message, halign="center"))
    row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
    pop = Popup(title=title, content=box, size_hint=(0.85, 0.4))
    yes, no = Button(text="Đồng ý"), Button(text="Hủy")
    yes.bind(on_release=lambda *_: (pop.dismiss(), on_yes()))
    no.bind(on_release=pop.dismiss)
    row.add_widget(yes)
    row.add_widget(no)
    box.add_widget(row)
    pop.open()


def store():
    return App.get_running_app().store


def ok(text):
    return f"[color=6fdc8c]{text}[/color]"


def bad(text):
    return f"[color=ff6b6b]{text}[/color]"


class Root(BoxLayout):
    pass


class PlayerTab(BoxLayout):
    balance_text = StringProperty("")
    result_text = StringProperty("Chọn trò chơi, cửa cược và mức cược rồi bấm đổ xúc xắc.")
    history_text = StringProperty("")

    def on_kv_post(self, base_widget):
        self.ids.game.values = list(core.GAMES)
        self.ids.game.text = list(core.GAMES)[0]
        self.refresh()

    def on_game(self, game):
        if game in core.GAMES:
            choices = core.GAMES[game]
            self.ids.choice.values = choices
            self.ids.choice.text = choices[0]

    def set_amount(self, value):
        self.ids.amount.text = str(store().balance if value < 0 else value)

    def refresh(self):
        s = store()
        self.balance_text = f"{money(s.balance)} xu"
        lines = []
        for h in s.history(30):
            t = time.strftime("%H:%M", time.localtime(h["ts"]))
            color = "6fdc8c" if h["delta"] > 0 else "ff6b6b"
            sign = "+" if h["delta"] > 0 else "-"
            lines.append(
                f"[color={color}]{t} {h['game']} · {h['choice']} {money(h['amount'])} → "
                f"{h['detail']} · {sign}{money(abs(h['delta']))}[/color]"
            )
        self.history_text = "\n".join(lines) or "Chưa có ván nào."

    def play(self):
        self.ids.play_btn.disabled = True
        self.result_text = "Đang lắc xúc xắc..."
        args = (self.ids.game.text, self.ids.choice.text, self.ids.amount.text)
        Clock.schedule_once(lambda dt: self._finish(*args), 0.7)

    def _finish(self, game, choice, amount):
        try:
            r = store().play(game, choice, amount)
        except GameError as e:
            self.result_text = bad(str(e))
        else:
            verdict = "THẮNG" if r["win"] else "THUA"
            color = "6fdc8c" if r["win"] else "ff6b6b"
            self.result_text = (
                f"{r['dice']}\n{r['outcome']}\n"
                f"[b][color={color}]{verdict} {money(abs(r['delta']))} xu[/color][/b]"
            )
        self.ids.play_btn.disabled = False
        App.get_running_app().refresh_all()

    def redeem(self):
        try:
            amount = store().redeem(self.ids.gift.text)
        except GameError as e:
            self.result_text = bad(str(e))
        else:
            self.result_text = ok(f"Đổi code thành công: +{money(amount)} xu")
            self.ids.gift.text = ""
        App.get_running_app().refresh_all()


class AdminLock(BoxLayout):
    tab = ObjectProperty(None)
    message = StringProperty("")

    def unlock(self):
        if store().check_pin(self.ids.pin.text):
            self.tab.show_panel()
        else:
            self.message = bad("Sai PIN")
            self.ids.pin.text = ""


class AdminPanel(BoxLayout):
    tab = ObjectProperty(None)
    stats_text = StringProperty("")
    gifts_text = StringProperty("")
    status = StringProperty("")

    def on_kv_post(self, base_widget):
        self.refresh()

    def refresh(self):
        s = store()
        st = s.stats()
        per = ", ".join(f"{g}: {n}" for g, n in st["per_game"].items()) or "chưa có"
        self.stats_text = (
            f"Số dư: {money(s.balance)} xu\n"
            f"Số ván: {st['rounds']} (thắng {st['wins']} / thua {st['losses']})\n"
            f"Lãi/lỗ tổng: {money(st['net']) if st['net'] >= 0 else '-' + money(-st['net'])} xu\n"
            f"Thắng lớn nhất: {money(st['best'])} xu\n"
            f"Theo trò: {per}"
        )
        gifts = s.list_gifts()
        self.gifts_text = "\n".join(
            f"{g['code']}: {money(g['amount'])} xu ({g['used']}/{g['max_uses']} lượt)" for g in gifts
        ) or "Chưa có gifcode."

    def _run(self, fn, success):
        try:
            result = fn()
        except GameError as e:
            self.status = bad(str(e))
            return
        except OSError as e:
            self.status = bad(f"Lỗi ghi file: {e}")
            return
        self.status = ok(success(result) if callable(success) else success)
        App.get_running_app().refresh_all()

    def set_balance(self):
        self._run(lambda: store().set_balance(self.ids.bal.text), "Đã cập nhật số xu")

    def create_gift(self):
        i = self.ids
        self._run(lambda: store().create_gift(i.g_code.text, i.g_amount.text, i.g_uses.text),
                  "Đã lưu gifcode")

    def delete_gift(self):
        self._run(lambda: store().delete_gift(self.ids.g_code.text), "Đã xóa gifcode")

    def export_csv(self):
        path = os.path.join(App.get_running_app().user_data_dir, "lich_su_luckdice.csv")
        self._run(lambda: store().export_csv(path), lambda n: f"Đã xuất {n} ván ra:\n{path}")

    def reset(self):
        confirm("Reset", "Xóa lịch sử và đặt lại số xu ban đầu?",
                lambda: self._run(store().reset_all, "Đã reset"))

    def change_pin(self):
        def do():
            store().set_pin(self.ids.new_pin.text)
            self.ids.new_pin.text = ""
        self._run(do, "Đã đổi PIN")


class AdminTab(BoxLayout):
    def on_kv_post(self, base_widget):
        self.show_lock()

    def show_lock(self):
        self.clear_widgets()
        self.add_widget(AdminLock(tab=self))

    def show_panel(self):
        self.clear_widgets()
        self.add_widget(AdminPanel(tab=self))

    def refresh(self):
        for child in self.children:
            if isinstance(child, AdminPanel):
                child.refresh()


class LuckDiceApp(App):
    title = "Luck Dice Offline"

    def build(self):
        # Nếu chữ tiếng Việt bị lỗi ô vuông, thêm file data/font.ttf (vd. NotoSans-Regular.ttf)
        font = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "font.ttf")
        if os.path.exists(font):
            LabelBase.register(DEFAULT_FONT, font)
        Window.softinput_mode = "below_target"
        self.store = core.Store(os.path.join(self.user_data_dir, "luckdice.db"))
        Builder.load_string(KV)
        return Root()

    def refresh_all(self):
        self.root.ids.player.refresh()
        self.root.ids.admin.refresh()


if __name__ == "__main__":
    LuckDiceApp().run()
