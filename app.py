import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def extract_transactions_from_pdf(file):
    rows = []
    current = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            for line in lines:
                if re.match(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', line):
                    if current:
                        rows.append(current)
                    current = [line]
                else:
                    current.append(line)
            if current:
                rows.append(current)

    results = []
    for r in rows:
        try:
            tanggal = r[0].split(' ')[0]
            angka_line = next((l for l in r if '-' in l and re.search(r'\d', l)), '')
            if not angka_line:
                continue
            parts = angka_line.strip().split()
            floats = []
            for p in parts:
                try:
                    val = float(p.replace('.', '').replace(',', '.'))
                    floats.append(val)
                except:
                    continue
            if len(floats) >= 3:
                debit, kredit, saldo = floats[-3], floats[-2], floats[-1]
            else:
                continue
            deskripsi = ' '.join([l for l in r[1:] if l != angka_line]).strip()
            results.append([tanggal, deskripsi, debit, kredit, saldo])
        except:
            continue

    df = pd.DataFrame(results, columns=['Tanggal', 'Deskripsi', 'Debit', 'Kredit', 'Saldo'])
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], format='%d/%m/%Y', errors='coerce')
    return df

def convert_df_to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')
    return buffer.getvalue()

def main():
    st.title("Konversi Rekening Mandiri ke Excel")
    st.write("Aplikasi ini mengonversi data rekening Mandiri menjadi file Excel.")

    uploaded = st.file_uploader("Unggah PDF Rekening Mandiri", type="pdf")
    if uploaded:
        df = extract_transactions_from_pdf(uploaded)
        st.dataframe(df)

        excel = convert_df_to_excel(df)
        st.download_button("Unduh Excel", data=excel, file_name="Rekening_Mandiri.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == '__main__':
    main()
