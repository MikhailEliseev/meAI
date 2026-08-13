"""Сравнить чат-ответ и отчёт по ключевым метрикам и наративу."""
import re


def grab(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def metrics(txt):
    return {
        "mln": sorted(set(re.findall(r"\d{2,4}\s*млн", txt))),
        "ratings": sorted(set(re.findall(r"\d[.,]\d\s*★", txt))),
        "reviews": sorted(set(re.findall(r"\d{2,5}\s*отзыв", txt))),
    }


chat = grab("/opt/data/chat_arclinic.txt")
# отчёт из WP
import subprocess

r = subprocess.run(
    ["sh", "-c", "cat /tmp/arclinic.html 2>/dev/null"],
    capture_output=True, text=True,
)
report_html = r.stdout
# strip tags
report_html = re.sub(r"<style[^>]*>.*?</style>", "", report_html, flags=re.S | re.I)
report_html = re.sub(r"</(p|div|h[1-4]|li|tr|td|th|section)>", "\n", report_html, flags=re.I)
report = re.sub(r"<[^>]+>", "", report_html)

print("=== ЧАТ метрики ===")
for k, v in metrics(chat).items():
    print("  %s: %s" % (k, v))
print("\n=== ОТЧЁТ метрики ===")
for k, v in metrics(report).items():
    print("  %s: %s" % (k, v))

print("\n=== ЧАТ: позиция/рекомендации (наратив) ===")
m = re.search(r"Позици[я].*?(?:Рекомендации|\Z)", chat, re.S | re.I)
print((m.group(0)[:700] if m else "(нет)")[:700])

print("\n=== ОТЧЁТ: позиция/рекомендации (наратив) ===")
m = re.search(r"Позици[я].*?(?:Рекомендации|\Z)", report, re.S | re.I)
print((m.group(0)[:700] if m else "(нет)")[:700])
