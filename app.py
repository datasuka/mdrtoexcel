import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def parse_amount(text):
    try:
        return float(text.replace('.', '').replace(',', '.').replace('−', '-'))
    except:
        return 0.0

def extract_transactions(file):
    transaksi = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')

            current_block = []
            for line in lines:
                # Cek baris pembuka transaksi
                if re.match(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$', line.strip()):
                    if current_block:
                        transaksi.append(current_block)
                    current_block = [line.strip()]
                else:
                    current_block.append(line.strip())
            if current_block:
                transaksi.append(current_block)

    hasil = []
    for block in transaksi:
        try:
            waktu_line = block[0]
            tanggal, jam = waktu_line.split()
            waktu_transaksi = f"{tanggal} {jam}"

            # Baris angka (biasanya di akhir blok)
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

            # Ambil deskripsi: semua baris kecuali waktu dan angka
            deskripsi = ' '.join([
                l for l in block[1:] if l.strip() and l.strip() != angka_line.strip()
            ])

            hasil.append([waktu_transaksi, deskripsi, debit, kredit, saldo])
        except:
            continue

    df = pd.DataFrame(hasil, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna()

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return output.getvalue()

def main():
    st.set_page_config(page_title="Ekstraksi PDF Rekening Mandiri", layout="centered")
    st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF", type=["pdf"])

    if uploaded:
        df = extract_transactions(uploaded)

        if df.empty:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"✅ {len(df)} transaksi berhasil diekstrak.")
            st.dataframe(df)

            excel_file = convert_df_to_excel(df)
            st.download_button(
                label="📥 Unduh Excel",
                data=excel_file,
                file_name="Rekening_Mandiri.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
