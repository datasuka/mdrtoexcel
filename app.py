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
    rows = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                if re.match(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$', line):
                    waktu = line
                    deskripsi_lines = []
                    angka_line = None

                    # Ambil sampai 5 baris deskripsi atau sampai ketemu angka
                    for j in range(1, 6):
                        if i + j >= len(lines):
                            break
                        candidate = lines[i + j].strip()
                        if len(re.findall(r'-?[\d.,]+', candidate)) >= 3:
                            angka_line = candidate
                            i += j
                            break
                        else:
                            deskripsi_lines.append(candidate)

                    if angka_line:
                        angka = re.findall(r'-?[\d.,]+', angka_line)
                        if len(angka) >= 3:
                            debit = parse_amount(angka[-3])
                            kredit = parse_amount(angka[-2])
                            saldo = parse_amount(angka[-1])
                            deskripsi = ' '.join(deskripsi_lines)
                            rows.append([waktu, deskripsi, debit, kredit, saldo])
                i += 1

    df = pd.DataFrame(rows, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna()

def convert_df_to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')
    return buffer.getvalue()

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
