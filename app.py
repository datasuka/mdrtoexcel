import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re


def parse_amount(text):
    """Konversi angka format Indonesia (1.000,00) ke float"""
    text = text.replace('.', '').replace(',', '.')
    try:
        return float(text)
    except:
        return 0.0


def extract_transactions(file):
    transactions = []
    with pdfplumber.open(file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            st.subheader(f"[DEBUG] Halaman {page_num}")
            st.text(text[:3000])  # tampilkan sebagian isi PDF (debug)

            lines = text.split('\n')
            temp_block = []

            for line in lines:
                if re.match(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', line):
                    if temp_block:
                        transactions.append(temp_block)
                    temp_block = [line]
                else:
                    temp_block.append(line)
            if temp_block:
                transactions.append(temp_block)

    data = []
    for trx in transactions:
        try:
            date_time = trx[0].strip().split()
            tanggal, waktu = date_time[0], date_time[1]
            deskripsi = ' '.join(trx[1:-1]).strip()
            angka_line = trx[-1]

            # Tangani baris angka (misalnya: "- 25,000,000.00 0.00 52,399,575.35")
            angka_parts = angka_line.replace('-', ' -').split()
            angka_floats = [parse_amount(a) for a in angka_parts if re.search(r'\d', a)]

            if len(angka_floats) == 3:
                debit, kredit, saldo = angka_floats
                data.append([tanggal, waktu, deskripsi, debit, kredit, saldo])
        except Exception as e:
            continue

    df = pd.DataFrame(data, columns=["Tanggal", "Waktu", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], format="%d/%m/%Y", errors='coerce')
    return df.dropna(subset=["Tanggal"])


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

        if df.empty:
            st.warning("Tidak ada transaksi berhasil diekstrak.")
        else:
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
