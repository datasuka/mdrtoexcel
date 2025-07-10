
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
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue

                headers = [h.lower() if h else '' for h in table[0]]
                for row in table[1:]:
                    if len(row) != len(headers):
                        continue
                    row_dict = dict(zip(headers, row))
                    tanggal_str = (row_dict.get('posting date') or '').strip()
                    keterangan = (row_dict.get('remark') or '').strip().lstrip('-').strip()
                    debit_str = (row_dict.get('debit') or '0').replace(',', '').replace('.', '')
                    credit_str = (row_dict.get('credit') or '0').replace(',', '').replace('.', '')
                    saldo_str = (row_dict.get('balance') or '0').replace(',', '').replace('.', '')

                    try:
                        tanggal = datetime.strptime(tanggal_str, '%d %b %Y, %H:%M:%S')
                    except:
                        tanggal = None

                    try:
                        debit = float(debit_str) / 100
                        credit = float(credit_str) / 100
                        saldo = float(saldo_str) / 100
                    except:
                        debit, credit, saldo = 0.0, 0.0, 0.0

                    rows.append({
                        'tanggal': tanggal,
                        'keterangan': keterangan,
                        'debit': debit,
                        'kredit': credit,
                        'saldo': saldo
                    })
    except Exception as e:
        st.warning(f"File gagal dibaca: {e}")

    return pd.DataFrame(rows)

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        st.write(f"Memproses: {file.name}")
        df = parse_mandiri_table(file)
        if not df.empty:
            all_dfs.append(df)
        else:
            st.warning(f"Tidak ada data ditemukan di: {file.name}")

    if all_dfs:
        df_final = pd.concat(all_dfs, ignore_index=True).sort_values(by=['tanggal'])

        # Format tampilan angka dengan koma
        df_display = df_final.copy()
        for col in ['debit', 'kredit', 'saldo']:
            df_display[col] = df_display[col].map(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        st.dataframe(df_display)

        buffer = BytesIO()
        df_final.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button("Download Excel", buffer, file_name="Mandiri_Excel.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Tidak ada data yang berhasil diproses.")
