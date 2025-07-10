
import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Mandiri PDF ke Excel", layout="wide")
st.title("Konversi Rekening Koran Mandiri (PDF) ke Excel")

uploaded_files = st.file_uploader("Upload file PDF Rekening Koran Mandiri", type="pdf", accept_multiple_files=True)

def parse_amount(text):
    try:
        return float(text.replace(',', '').replace('.', '').replace(',', '.'))
    except:
        return 0.0

def parse_mandiri_table(pdf_file):
    rows = []
    account_number = None
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not account_number and 'Account No.' in text:
                    match = re.search(r'Account No\.\s+(\d+)', text)
                    if match:
                        account_number = match.group(1)

                table = page.extract_table()
                if not table:
                    continue

                headers = [h.lower() for h in table[0]]
                for row in table[1:]:
                    row_dict = dict(zip(headers, row))
                    tanggal_str = row_dict.get('posting date', '').strip()
                    keterangan = (row_dict.get('remark') or '').strip().lstrip('-').strip()
                    debit_str = (row_dict.get('debit') or '0').replace(',', '').replace('.', '')
                    credit_str = (row_dict.get('credit') or '0').replace(',', '').replace('.', '')
                    saldo_str = (row_dict.get('balance') or '0').replace(',', '').replace('.', '')

                    # Ambil tanggal + waktu
                    try:
                        tanggal = datetime.strptime(tanggal_str, '%d %b %Y, %H:%M:%S')
                    except:
                        tanggal = None

                    debit = float(debit_str) / 100
                    credit = float(credit_str) / 100
                    saldo = float(saldo_str) / 100

                    rows.append({
                        'no_rekening': account_number,
                        'tanggal': tanggal,
                        'keterangan': keterangan,
                        'debit': debit,
                        'kredit': credit,
                        'saldo': saldo
                    })
    except Exception as e:
        st.error(f"Gagal memproses file: {e}")

    return pd.DataFrame(rows)

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        st.write(f"Memproses: {file.name}")
        df = parse_mandiri_table(file)
        all_dfs.append(df)

    if all_dfs:
        df_final = pd.concat(all_dfs).sort_values(by=['no_rekening', 'tanggal'])

        # Format angka dengan koma desimal (untuk tampilan)
        df_display = df_final.copy()
        for col in ['debit', 'kredit', 'saldo']:
            df_display[col] = df_display[col].map(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        st.dataframe(df_display)

        # Simpan Excel (angka tetap dalam float)
        buffer = BytesIO()
        df_final.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button("Download Excel", buffer, file_name="Mandiri_Excel.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
