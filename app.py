import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def parse_amount(text):
    """Konversi teks angka Indonesia ke float"""
    text = text.replace('.', '').replace(',', '.')
    try:
        return float(text)
    except:
        return 0.0

def extract_transactions(file):
    data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            trx = []
            for line in lines:
                if re.match(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', line):
                    if trx:
                        data.append(trx)
                    trx = [line]
                else:
                    trx.append(line)
            if trx:
                data.append(trx)

    extracted = []
    for trx in data:
        try:
            date_time = trx[0].split()
            tanggal = date_time[0]
            waktu = date_time[1]
            deskripsi = ' '.join(trx[1:-1]).strip()
            angka_line = trx[-1]

            # Pecah baris angka, bisa saja dengan tanda minus terpisah
            angka_parts = angka_line.replace('-', ' -').split()
            angka_float = [parse_amount(a) for a in angka_parts if re.search(r'\d', a)]

            if len(angka_float) == 3:
                debit, kredit, saldo = angka_float
                extracted.append([tanggal, waktu, deskripsi, debit, kredit, saldo])
        except Exception as e:
            continue

    df = pd.DataFrame(extracted, columns=["Tanggal", "Waktu", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], format="%d/%m/%Y", errors='coerce')
    return df

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')
    return output.getvalue()

def main():
    st.set_page_config(page_title="Ekstraksi Rekening Mandiri", layout="centered")
    st.title("Ekstraksi Rekening Mandiri ke Excel")
    uploaded = st.file_uploader("Unggah PDF Rekening Mandiri", type="pdf")

    if uploaded:
        df = extract_transactions(uploaded)
        st.success(f"Berhasil mengekstrak {len(df)} transaksi.")
        st.dataframe(df)

        excel = convert_df_to_excel(df)
        st.download_button(
            "Unduh Excel",
            data=excel,
            file_name="Rekening_Mandiri.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
