import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re


def parse_amount(text):
    """Ubah format angka lokal (1.000,00) jadi float"""
    try:
        return float(text.replace('.', '').replace(',', '.'))
    except:
        return 0.0


def extract_transactions(file):
    rows = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            st.text_area("DEBUG - Isi Halaman PDF", text[:3000], height=250)

            lines = text.split('\n')

            for line in lines:
                # Cari pola: tanggal waktu deskripsi nominal debit kredit saldo
                match = re.search(
                    r'(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2}) (.+?) (-?\d[\d.,]*) (-?\d[\d.,]*) (-?\d[\d.,]*)$',
                    line
                )
                if match:
                    tanggal = match.group(1)
                    waktu = match.group(2)
                    deskripsi = match.group(3).strip()
                    debit = parse_amount(match.group(4))
                    kredit = parse_amount(match.group(5))
                    saldo = parse_amount(match.group(6))
                    rows.append([tanggal, waktu, deskripsi, debit, kredit, saldo])

    df = pd.DataFrame(rows, columns=["Tanggal", "Waktu", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], format="%d/%m/%Y", errors="coerce")
    return df.dropna(subset=["Tanggal"])


def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return output.getvalue()


def main():
    st.set_page_config(page_title="Ekstraksi Rekening Mandiri", layout="centered")
    st.title("Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF Rekening Mandiri", type="pdf")

    if uploaded:
        df = extract_transactions(uploaded)

        if df.empty:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"✅ {len(df)} transaksi berhasil diekstrak.")
            st.dataframe(df)

            excel_data = convert_df_to_excel(df)
            st.download_button(
                label="📥 Unduh Excel",
                data=excel_data,
                file_name="Rekening_Mandiri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


if __name__ == "__main__":
    main()
