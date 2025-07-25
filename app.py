import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def parse_amount(text):
    try:
        return float(text.replace('.', '').replace(',', '.'))
    except:
        return 0.0

def extract_transactions(file):
    rows = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            current_block = []

            for line in lines:
                # Deteksi baris pembuka transaksi
                if re.match(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$', line.strip()):
                    if current_block:
                        rows.append(current_block)
                    current_block = [line.strip()]
                else:
                    current_block.append(line.strip())

            if current_block:
                rows.append(current_block)

    data = []
    for block in rows:
        try:
            waktu_line = block[0]
            tanggal, waktu = waktu_line.split(' ')

            # Ambil baris angka terakhir yang punya 3 angka
            angka_line = next(
                (l for l in reversed(block) if len(re.findall(r'-?[\d.,]+', l)) >= 3),
                None
            )
            if not angka_line:
                continue

            angka = re.findall(r'-?[\d.,]+', angka_line)
            if len(angka) < 3:
                continue

            debit = parse_amount(angka[-3])
            kredit = parse_amount(angka[-2])
            saldo = parse_amount(angka[-1])

            # Ambil semua baris selain waktu & angka sebagai deskripsi
            deskripsi = ' '.join([
                l for l in block[1:]
                if l and l.strip() != angka_line.strip()
            ])

            data.append([f"{tanggal} {waktu}", deskripsi.strip(), debit, kredit, saldo])
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
