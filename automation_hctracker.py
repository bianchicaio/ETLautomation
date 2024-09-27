import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import time

# Definir datas de início dos batches
BATCHES = [
    {"start": (1, 3), "end": (4, 5)},
    {"start": (4, 6), "end": (7, 8)},
    {"start": (7, 9), "end": (10, 11)},
    {"start": (10, 12), "end": (1, 2)},
]

def get_current_batch_and_week(current_date):
    current_year = current_date.year
    batch_start = None

    for batch in BATCHES:
        batch_start_date = datetime(current_year, batch["start"][0], batch["start"][1])
        if current_date >= batch_start_date:
            batch_start = batch_start_date
        else:
            break
    
    if batch_start is None:
        batch_start = datetime(current_year - 1, BATCHES[-1]["start"][0], BATCHES[-1]["start"][1])

    week_number = ((current_date - batch_start).days // 7) + 1

    start_of_week = batch_start + timedelta(weeks=week_number - 1)
    end_of_week = start_of_week + timedelta(days=6)
    
    return batch_start, week_number, start_of_week, end_of_week

async def main():
    today = datetime.today()
    day_of_week = today.weekday()

    # Verifica se é segunda-feira (0) ou sexta-feira (4)
    if day_of_week == 0:
        # Terça-feira: Seleciona a semana anterior
        target_date = today - timedelta(days=7)
        print("Segunda: Selecionando a semana anterior.")
    elif day_of_week == 4:
        # Sexta-feira: Seleciona a semana atual
        target_date = today
        print("Sexta-feira: Selecionando a semana atual.")
    else:
        print("Hoje não é segunda-feira nem sexta-feira, o bot não será executado.")
        return

    # Obtém o batch, semana e datas de início e fim
    batch_start, week_number, start_of_week, end_of_week = get_current_batch_and_week(target_date)
    
    # Formata as datas para o menu de seleção
    formatted_week = f"week {week_number} ({start_of_week.strftime('%m/%d')} ~ {end_of_week.strftime('%m/%d')}) {start_of_week.year}-"
    print(f"Selecionando a semana: {formatted_week}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="datapower_auth.json")
        page = await context.new_page()
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        await page.goto("https://byteworks-va.bytelemon.com/hc/bpo-available-fte")
        await page.locator("div").filter(has_text=re.compile(r"^FTE Entry$")).nth(1).click()
        print("Clicou em FTE Entry")
        await page.locator("li").filter(has_text="BPO Available FTE").click()
        print("Selecionou BPO Available FTE")

        await page.get_by_label("Cascader").click()
        await page.get_by_role("menuitem", name=re.compile(f"week {week_number}.*")).click()  # Seleciona a semana correta
        print(f"Selecionou a semana: {formatted_week}")

        await page.get_by_role("button", name="filter Advanced Filters 10").click()
        await page.get_by_label("Category").get_by_text("Please select").click()
        await page.get_by_role("option", name="tick ADSO").click()
        await page.get_by_role("option", name="tick Emerging").click()
        await page.get_by_role("option", name="tick Live").click()
        await page.get_by_role("option", name="tick TikTok").click()
        await page.get_by_role("button", name="Apply").click()
        print("Selecionou os Filtros")
        time.sleep(6)
        await page.get_by_role("button", name="more").click()
        # Inicia o download e espera que ele termine
        async with page.expect_download() as download_info:
            await page.get_by_role("menuitem", name="export Export").click()
            print("Iniciou o download")

        download = await download_info.value
        await download.save_as(os.path.join(download_path, download.suggested_filename))
        print(f"Arquivo baixado e salvo em: {os.path.join(download_path, download.suggested_filename)}")
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
