"""Luck Dice Offline - logic trò chơi + lưu trữ SQLite.

Chỉ dùng "xu" ảo, chạy hoàn toàn trên máy, kết quả xúc xắc ngẫu nhiên thật
(random.SystemRandom). Không có server, không có chỉnh kết quả.
"""
import csv
import hashlib
import os
import random
import sqlite3
import time

_rng = random.SystemRandom()

START_BALANCE = 100_000
MIN_BET = 1_000
DEFAULT_PIN = "1234"

BAU_CUA = ["Bầu", "Cua", "Tôm", "Cá", "Gà", "Nai"]  # mặt xúc xắc 1..6
GAMES = {
    "Tài Xỉu": ["Tài", "Xỉu"],
    "Chẵn Lẻ": ["Chẵn", "Lẻ"],
    "Bầu Cua": BAU_CUA,
}


class GameError(Exception):
    """Lỗi hiển thị được cho người chơi."""


def money(n):
    return f"{int(n):,}".replace(",", ".")


def _hash_pin(pin, salt):
    return hashlib.sha256((salt + pin).encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path):
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL, game TEXT, choice TEXT, amount INTEGER,
                detail TEXT, delta INTEGER, balance_after INTEGER);
            CREATE TABLE IF NOT EXISTS gifcodes(
                code TEXT PRIMARY KEY, amount INTEGER, max_uses INTEGER, used INTEGER DEFAULT 0);
            """
        )
        if self._get("balance") is None:
            self._set("balance", str(START_BALANCE))
        if self._get("pin_hash") is None:
            self.set_pin(DEFAULT_PIN)
            self.create_gift("WELCOME", 50_000, 3)
        self.db.commit()

    # ---------- settings ----------
    def _get(self, key):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def _set(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value)))

    # ---------- ví ----------
    @property
    def balance(self):
        return int(self._get("balance"))

    def set_balance(self, amount):
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            raise GameError("Số xu không hợp lệ")
        if amount < 0:
            raise GameError("Số xu không được âm")
        self._set("balance", amount)
        self.db.commit()

    # ---------- chơi ----------
    def play(self, game, choice, amount):
        if game not in GAMES:
            raise GameError("Trò chơi không hợp lệ")
        if choice not in GAMES[game]:
            raise GameError("Hãy chọn cửa cược")
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            raise GameError("Nhập số xu cược")
        if amount < MIN_BET:
            raise GameError(f"Cược tối thiểu {money(MIN_BET)} xu")
        bal = self.balance
        if amount > bal:
            raise GameError("Không đủ xu")

        if game == "Tài Xỉu":
            dice = [_rng.randint(1, 6) for _ in range(3)]
            total = sum(dice)
            if dice[0] == dice[1] == dice[2]:
                outcome, win = f"Tổng {total} - BÃO (nhà cái ăn)", False
            else:
                res = "Tài" if total >= 11 else "Xỉu"
                outcome, win = f"Tổng {total} - {res}", res == choice
            delta = amount if win else -amount
            dice_text = " - ".join(map(str, dice))
        elif game == "Chẵn Lẻ":
            dice = [_rng.randint(1, 6) for _ in range(2)]
            total = sum(dice)
            res = "Chẵn" if total % 2 == 0 else "Lẻ"
            outcome, win = f"Tổng {total} - {res}", res == choice
            delta = amount if win else -amount
            dice_text = " - ".join(map(str, dice))
        else:  # Bầu Cua
            dice = [_rng.randint(1, 6) for _ in range(3)]
            faces = [BAU_CUA[d - 1] for d in dice]
            hits = faces.count(choice)
            win = hits > 0
            delta = amount * hits if win else -amount
            outcome = f"Trúng {hits} lần" if win else "Không trúng"
            dice_text = " - ".join(faces)

        new_bal = bal + delta
        self._set("balance", new_bal)
        detail = f"{dice_text} | {outcome}"
        self.db.execute(
            "INSERT INTO history(ts,game,choice,amount,detail,delta,balance_after) VALUES(?,?,?,?,?,?,?)",
            (time.time(), game, choice, amount, detail, delta, new_bal),
        )
        self.db.commit()
        return {"dice": dice_text, "outcome": outcome, "win": win, "delta": delta, "balance": new_bal}

    # ---------- lịch sử / thống kê ----------
    def history(self, limit=30):
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,))]

    def stats(self):
        rows = [dict(r) for r in self.db.execute("SELECT game, delta FROM history")]
        wins = [r for r in rows if r["delta"] > 0]
        per_game = {}
        for r in rows:
            per_game[r["game"]] = per_game.get(r["game"], 0) + 1
        return {
            "rounds": len(rows),
            "wins": len(wins),
            "losses": len(rows) - len(wins),
            "net": sum(r["delta"] for r in rows),
            "best": max((r["delta"] for r in wins), default=0),
            "per_game": per_game,
        }

    def export_csv(self, path):
        rows = self.db.execute("SELECT * FROM history ORDER BY id").fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["id", "thoi_gian", "tro_choi", "cua_cuoc", "xu_cuoc", "ket_qua", "thay_doi", "so_du"])
            for r in rows:
                w.writerow([r["id"], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["ts"])),
                            r["game"], r["choice"], r["amount"], r["detail"], r["delta"], r["balance_after"]])
        return len(rows)

    # ---------- gifcode ----------
    @staticmethod
    def _norm_code(code):
        code = (code or "").strip().upper()
        if not (3 <= len(code) <= 20) or not code.isalnum():
            raise GameError("Gifcode gồm 3-20 chữ/số, không dấu")
        return code

    def create_gift(self, code, amount, max_uses):
        code = self._norm_code(code)
        try:
            amount, max_uses = int(amount), int(max_uses)
        except (TypeError, ValueError):
            raise GameError("Số xu / số lần dùng không hợp lệ")
        if amount <= 0 or max_uses <= 0:
            raise GameError("Số xu và số lần dùng phải > 0")
        self.db.execute("INSERT OR REPLACE INTO gifcodes(code,amount,max_uses,used) VALUES(?,?,?,0)",
                        (code, amount, max_uses))
        self.db.commit()

    def delete_gift(self, code):
        code = self._norm_code(code)
        cur = self.db.execute("DELETE FROM gifcodes WHERE code=?", (code,))
        self.db.commit()
        if cur.rowcount == 0:
            raise GameError("Không có gifcode này")

    def list_gifts(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM gifcodes ORDER BY code")]

    def redeem(self, code):
        code = self._norm_code(code)
        row = self.db.execute("SELECT * FROM gifcodes WHERE code=?", (code,)).fetchone()
        if row is None:
            raise GameError("Gifcode không tồn tại")
        if row["used"] >= row["max_uses"]:
            raise GameError("Gifcode đã hết lượt dùng")
        self.db.execute("UPDATE gifcodes SET used=used+1 WHERE code=?", (code,))
        self._set("balance", self.balance + row["amount"])
        self.db.commit()
        return row["amount"]

    # ---------- admin PIN / reset ----------
    def check_pin(self, pin):
        return _hash_pin(pin or "", self._get("pin_salt")) == self._get("pin_hash")

    def set_pin(self, pin):
        pin = (pin or "").strip()
        if len(pin) < 4:
            raise GameError("PIN tối thiểu 4 ký tự")
        salt = os.urandom(8).hex()
        self._set("pin_salt", salt)
        self._set("pin_hash", _hash_pin(pin, salt))
        self.db.commit()

    def reset_all(self):
        self.db.execute("DELETE FROM history")
        self._set("balance", START_BALANCE)
        self.db.commit()
