import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def parse_amount(text):
    """Konversi format angka Indonesia ke float"""
    try:
        return float(text.replace('.', '').replace(',', '.'))
    except:
        return 0.0

def extract_transactions(file):
    rows = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            st.text_area("DEBUG - Isi PDF", text[:3000], height=250)
            lines = text.split('\n')
            current_block = []

            for line in lines:
                if re.match(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', line):
                    if current_block:
                        rows.append(current_block)
                    current_block = [line]
                else:
                    current_block.append(line)

            if current_block:
                rows.append(current_block)

    data = []
    for block in rows:
        try:
            header = block[0]
            match = re.match(r'(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})', header)
            if not match:
                continue

            tanggal, waktu = match.group(1), match.group(2)
            angka_line = block[-1]
            angka = re.findall(r'-?[\d.,]+', angka_line)
            if len(angka) < 3:
                continue

            debit = parse_amount(angka[-3])
            kredit = parse_amount(angka[-2])
            saldo = parse_amount(angka[-1])

            deskripsi_lines = block[1:-1]
            deskripsi = ' '.join([line.strip() for line in deskripsi_lines if line.strip()])

            data.append([f"{tanggal} {waktu}", deskripsi, debit, kredit, saldo])
        except:
            continue

    df = pd.DataFrame(data, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna(subset=["Waktu Transaksi"])

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return output.getvalue()

def main():
    st.set_page_config(page_title="Ekstraksi Rekening Mandiri", layout="centered")
    st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF", type="pdf")

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
