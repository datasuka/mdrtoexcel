
import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Mandiri PDF ke Excel", layout="wide")
st.title("Konversi Rekening Koran Mandiri (PDF) ke Excel")

uploaded_files = st.file_uploader("Upload file PDF Rekening Koran Mandiri", type="pdf", accept_multiple_files=True)

lag_between_data = 15
remarks_left = 100
remarks_right = 300

def remove_sequence(text):
    match = re.search(r'^\d+', text)
    if match:
        return text[match.end():].strip()
    return text.strip()

def remove_excessive_space(text):
    return re.sub(r'\s+', ' ', text).strip()

def has_two_monetary_amounts(text):
    return len(re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", text)) >= 2

def has_time(text):
    return re.search(r"\d{2}:\d{2}:\d{2}", text)

def parse_mandiri_pdf(pdf_file, account_num_hint=""):
    data = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            account_num = account_num_hint
            for page in pdf.pages:
                words = page.extract_words()
                prev_top = 0
                remarks_top = 1000
                first_desc = ''

                trx_date = None
                trx_desc = ''
                trx_code = 'K'
                trx_amount = None
                trx_balance = None

                for word in words:
                    top = word['top']
                    top_lag = top - prev_top

                    if 'remark' in word['text'].lower():
                        remarks_top = top

                    if top > remarks_top:
                        if top_lag > lag_between_data:
                            if trx_date and trx_desc:
                                trx_desc = remove_sequence(re.sub(r'\d{2}:\d{2}:\d{2}\s+WIB', '', trx_desc))
                                trx_desc = remove_excessive_space(trx_desc)
                                data.append({
                                    'no_rekening': account_num,
                                    'tanggal': trx_date,
                                    'keterangan': trx_desc,
                                    'kode': trx_code,
                                    'mutasi': trx_amount,
                                    'saldo': trx_balance
                                })
                                trx_desc, trx_code, trx_amount, trx_balance = '', 'K', None, None

                            first_desc = word['text']

                        elif 0 < top_lag <= lag_between_data:
                            text = first_desc
                            date_match = re.search(r'(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Mei|Agu|Okt|Des) (\d{4})', text)
                            if date_match:
                                month_map = {'Jan': '01','Feb': '02','Mar': '03','Apr': '04','May': '05','Mei': '05','Jun': '06','Jul': '07','Aug': '08','Agu': '08','Sep': '09','Oct': '10','Nov': '11','Dec': '12','Des': '12','Okt': '10'}
                                dd, mm, yy = date_match.groups()
                                mm = month_map.get(mm, '01')
                                trx_date = datetime.strptime(f"{dd.zfill(2)}/{mm}/{yy}", "%d/%m/%Y")
                            if has_two_monetary_amounts(text):
                                amounts = re.findall(r"[+-]?\d{1,3}(?:\.\d{3})*,\d{2}", text)
                                if len(amounts) >= 2:
                                    trx_amount = amounts[0].replace('-', '').replace('+', '')
                                    trx_code = 'D' if amounts[0].startswith('-') else 'K'
                                    trx_balance = amounts[1]

                            first_desc = word['text']

                        elif top_lag <= 0:
                            first_desc += ' ' + word['text']

                        if remarks_left < word['x0'] < remarks_right:
                            trx_desc += ' ' + word['text']

                    prev_top = top

    except Exception as e:
        st.error(f"Error processing file: {e}")

    df = pd.DataFrame(data)
    if not df.empty:
        df['mutasi'] = df['mutasi'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        df['saldo'] = df['saldo'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    return df

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        st.write(f"Memproses: {file.name}")
        df_result = parse_mandiri_pdf(file)
        all_data.append(df_result)

    if all_data:
        df_final = pd.concat(all_data).sort_values(by=['no_rekening', 'tanggal'])
        st.dataframe(df_final)

        buffer = BytesIO()
        df_final.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button("Download Excel", buffer, file_name="Mandiri_Excel.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
