"""Сравнение чат-ответа и опубликованного отчёта — найти расхождения."""
import re
import sqlite3
import sys


def extract_numbers(txt):
    """Ключевые числа: выручка/прибыль (млн/млрд), рейтинги, отзывы."""
    nums = {
        "mln": sorted(set(re.findall(r"\d[\d\s]*\d\s*млн", txt))),
        "mlrd": sorted(set(re.findall(r"\d[\d\s]*\d\s*млрд", txt))),
        "ratings": sorted(set(re.findall(r"\d[.,]\d\s*★", txt))),
        "reviews": sorted(set(re.findall(r"\d{2,5}\s*отзыв", txt))),
    }
    return nums


def main():
    sid = "sess_1785264384878_qylrkf2bf"
    con = sqlite3.connect("/opt/data/sessions.db")
    cur = con.cursor()
    cur.execute(
        "SELECT content FROM messages WHERE session_id=? AND role='assistant' ORDER BY id DESC LIMIT 1",
        (sid,),
    )
    row = cur.fetchone()
    chat = row[0] if row else ""
    print("=== ЧАТ-ответ (длина %d) ===" % len(chat))
    cn = extract_numbers(chat)
    for k, v in cn.items():
        print("  %s: %s" % (k, v))
    print()
    print("=== первые 1000 символов чата ===")
    print(chat[:1000])
    # сохраним для сравнения
    with open("/opt/data/chat_arclinic.txt", "w") as f:
        f.write(chat)
    print("\n[saved to /opt/data/chat_arclinic.txt]")


if __name__ == "__main__":
    main()
