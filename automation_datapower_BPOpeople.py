import asyncio
import time
import pandas as pd
import os
import re
from datetime import datetime, timedelta
from playwright.async_api import Playwright, async_playwright, expect
import warnings
import win32com.client as win32  # Para envio de e-mails via Outlook
warnings.filterwarnings('ignore')

# Caminhos para pastas de dados
path1 = r"\\emea.tpg.ads\portugal\Departments\ITDEV\PowerBI\accounting\business analysts\01 - ba\02 - projects\tiktok\4. Raw Data and Aux Files\37. New DP Data\BPO_PEOPLE"
# Definindo o caminho de download como a pasta 'Downloads' do usuário
download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
# Criando um DataFrame para registrar o log de download
log_df = pd.DataFrame(columns=['Filename', 'Date', 'Status', 'Message'])

# Função para extrair datas do nome do arquivo
def extract_dates_from_filename(filename):
    match = re.search(r'(\d{2})(\d{2})(\d{4})_(\d{2})(\d{2})(\d{4})', filename)
    if match:
        # Extraindo partes da data do nome do arquivo
        day_start = match.group(1)
        month_start = match.group(2)
        year_start = match.group(3)
        day_end = match.group(4)
        month_end = match.group(5)
        year_end = match.group(6)
        
        # Convertendo as partes da data em objetos datetime
        start_date_obj = datetime.strptime(f"{day_start}{month_start}{year_start}", "%d%m%Y")
        end_date_obj = datetime.strptime(f"{day_end}{month_end}{year_end}", "%d%m%Y")
        
        # Formatando as datas como strings
        start_date = start_date_obj.strftime("%Y-%m-%d")
        end_date = end_date_obj.strftime("%Y-%m-%d")
        month_name = start_date_obj.strftime("%b")
        month_start_number = start_date_obj.strftime("%m")
        month_end_number = end_date_obj.strftime("%m")
        
        return start_date, end_date, day_start, day_end, month_name, month_start_number, month_end_number
    return None, None, None, None, None, None, None

# Função para obter intervalos de datas dos arquivos na pasta
def get_date_ranges_from_folder(folder_path, num_files):
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".csv")]

    date_ranges = []
    for file_path in files:
        filename = os.path.basename(file_path)
        start_date, end_date, day_start_only, day_end_only, month_name, month_start_number, month_end_number = extract_dates_from_filename(filename)
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            date_ranges.append((start_date_obj, end_date_obj, day_start_only, day_end_only, month_name, month_start_number, month_end_number))
    
    # Ordena os intervalos de datas em ordem decrescente e pega os últimos 'num_files' intervalos
    date_ranges.sort(key=lambda x: x[0], reverse=True)
    last_date_ranges = date_ranges[:num_files]

    # Imprime os intervalos de datas para verificação
    for start_date, end_date, day_start, day_end, month_end, month_start_number, month_end_number in last_date_ranges:
        print(f"Start Date: {start_date}, End Date: {end_date}, Start Day: {day_start}, End Day: {day_end}, End Month: {month_end}, Month Start Number: {month_start_number}, Month End Number: {month_end_number}")

    return last_date_ranges

# Função para executar a primeira parte do download dos arquivos
async def run_first_part(playwright: Playwright, start_date: str, end_date: str, day_start: str, day_end: str, month_end_number: str, download_path: str, log_df: pd.DataFrame) -> pd.DataFrame:
    print(f"Start Date in run_first_part: {start_date}, End Date in run_first_part: {end_date}")
    # Lança um novo navegador
    browser = await playwright.chromium.launch(headless=False)
    # Cria um novo contexto de navegação
    context = await browser.new_context(storage_state="datapower_auth.json")
    # Abre uma nova página
    page = await context.new_page()
    # Navega até a URL especificada
    await page.goto("https://datapower-va.bytelemon.com/operating/bpo_site_dashboard")

    # Interage com os elementos da página para configurar a busca (esses passos estão suspensos por já estarem presentes nos cookies)
    #await page.get_by_role("button", name="Time granularity Daily").click()
    #await page.get_by_role("option", name="tick Hourly").click()
    #await page.get_by_role("button", name="More filters 1 chevron_down").click()
    #await page.get_by_role("combobox", name="Department").click() 
    #await page.get_by_placeholder("Search", exact=True).click()
    #await page.get_by_placeholder("Search", exact=True).fill("mi")
    #await page.get_by_role("dialog").get_by_text("TP_LIS_MI", exact=True).click()
    #await page.get_by_role("combobox", name="Department").click()
    #await page.get_by_role("button", name="Application").click()
    #await page.get_by_role("button", name="search Search").click()

    # Localiza e rola até a tabela de estatísticas de moderação
    element = page.locator("text='Moderation Statistics Table'")
    await element.scroll_into_view_if_needed()
    await page.pause()
    await page.get_by_role("button", name="Column preset Basic Indicator").nth(1).click()
    await page.get_by_text("Workhour Indicators").click()
    await page.get_by_role("button", name="export Export data").nth(2).click()
    await page.get_by_role("menuitem", name="Export Custom Subunit Data").click()
        # Espera 2 segundos para garantir que o campo esteja preenchido
    time.sleep(2)
    await page.locator("#dialog-0").get_by_placeholder("End date").click()
    
    # Selecione o End Date
    await page.locator("#dialog-0").get_by_placeholder("End date").fill(f"{end_date}")
    
    #Selecione Star Date
    print(start_date)
    page.locator("#dialog-0").get_by_placeholder("Start date").press("Control+a")
    time.sleep(2)
    #await page.pause()
    await page.locator("#dialog-0").get_by_placeholder("Start date").fill(f"{start_date}")

    time.sleep(3)

    await page.get_by_role("button", name="Confirm", exact=True).click()
    await page.locator("label").filter(has_text="CSV(Maximum100w)").click()
    
    try:
        # Espera pelo download e salva o arquivo na pasta de download
        async with page.expect_download(timeout=1200000) as download_info:
            await page.get_by_label("confirm").click()
        download = await download_info.value

        suggested_filename = download.suggested_filename
        download_file_path = os.path.join(download_path, suggested_filename)
        await download.save_as(download_file_path)
        print(f"Download concluído. Arquivo salvo em: {download_file_path}")
        # Usar loc para adicionar uma nova linha ao DataFrame
        log_df.loc[len(log_df)] = {'Filename': suggested_filename, 'Date': f'{start_date} to {end_date}', 'Status': 'Success', 'Message': 'Download completed'}

    except Exception as e:
        print(f"Erro ao fazer download: {e}")
        # Usar loc para adicionar uma nova linha ao DataFrame
        log_df.loc[len(log_df)] = {'Filename': 'N/A', 'Date': f'{start_date} to {end_date}', 'Status': 'Fail', 'Message': str(e)}

    # Fecha o contexto e o navegador
    await context.close()
    await browser.close()
    return log_df

# Função para gerar intervalos de datas até ontem
def generate_date_ranges_until_yesterday(last_end_date):
    date_ranges = []
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_date = last_end_date + timedelta(days=1)
    # Gera intervalos de datas de dois dias até ontem
    while start_date < yesterday:
        end_date = start_date + timedelta(days=2)
        if end_date > yesterday:
            end_date = yesterday
        date_ranges.append((start_date, end_date))
        start_date = end_date + timedelta(days=1)

    return date_ranges

# Função para tentar novamente os downloads que falharam
async def retry_failed_downloads(playwright, download_path, log_df):
    failed_downloads = log_df[log_df['Status'] == 'Fail']
    if failed_downloads.empty:
        return log_df

    for _, row in failed_downloads.iterrows():
        date_range = row['Date']
        start_date, end_date = date_range.split(" to ")
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        day_start = start_date_obj.strftime("%d")
        day_end = end_date_obj.strftime("%d")
        month_end_number = end_date_obj.strftime("%m")

        log_df = await run_first_part(playwright, start_date + " 00", end_date + " 23", day_start, day_end, month_end_number, download_path, log_df)

    return log_df

# Função para enviar e-mails utilizando o Outlook
def send_email(log_df):
    try:
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.Subject = 'Relatório de Status dos Downloads'
        mail.To = 'caio.bechara@teleperformance.com'
        mail.CC = 'pedro.esteves@teleperformance.com'

        # Verifica se houve falhas nos downloads
        failure_logs = log_df[log_df['Status'] == 'Fail']
        if not failure_logs.empty:
            failure_details = "\n\n".join(failure_logs.apply(lambda row: f"Arquivo: {row['Filename']}\nData: {row['Date']}\nMensagem de Erro: {row['Message']}", axis=1).tolist())
            mail.Body = f"Os seguintes downloads falharam:\n\n{failure_details}"
        else:
            mail.Body = "Todos os downloads do arquivo BPO People foram bem-sucedidos.\n\nObrigado."

        mail.Send()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")

# Função principal
async def main():
    # Obtém os últimos cinco intervalos de datas da primeira pasta
    date_ranges_first_part = get_date_ranges_from_folder(path1, 5)
    date_ranges_first_part.sort(key=lambda x: x[0], reverse=False)

    global log_df

    async with async_playwright() as playwright:
        # Percorre os intervalos de datas e baixa os arquivos
        for start_date, end_date, day_start, day_end, month_name, month_start_number, month_end_number in date_ranges_first_part:
            print(f"Start Date in main: {start_date}, End Date in main: {end_date}")
            log_df = await run_first_part(playwright, start_date.strftime("%Y-%m-%d 00"), end_date.strftime("%Y-%m-%d 23"), day_start, day_end, month_end_number, download_path, log_df)

        last_downloaded_end_date = date_ranges_first_part[-1][1]
        additional_date_ranges = generate_date_ranges_until_yesterday(last_downloaded_end_date)

        for start_date, end_date in additional_date_ranges:
            print(f"Start Date in additional: {start_date}, End Date in additional: {end_date}")
            day_start = start_date.strftime("%d")
            day_end = end_date.strftime("%d")
            month_end_number = end_date.strftime("%m")
            log_df = await run_first_part(playwright, start_date.strftime("%Y-%m-%d 00"), end_date.strftime("%Y-%m-%d 23"), day_start, day_end, month_end_number, download_path, log_df)

        # Tenta novamente os downloads que falharam
        log_df = await retry_failed_downloads(playwright, download_path, log_df)

        # Envio de e-mail com o status dos downloads
        send_email(log_df)

    # Verifica se todos os downloads foram bem-sucedidos
    all_successful = log_df['Status'].eq('Success').all()
    if all_successful:
        print("Todos os downloads foram concluídos com sucesso.")
    else:
        print("Alguns downloads falharam.")

    return all_successful

# Executa a função principal
all_downloads_successful = asyncio.run(main())
if all_downloads_successful:
    print("Processo concluído sem erros.")
else:
    print("Processo concluído com erros.")
