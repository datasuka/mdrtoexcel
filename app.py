import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

def parse_float(val):
    try:
        return float(val.replace(".", "").replace(",", "."))
    except:
        return 0.0

def extract_transactions_from_pdf(file):
    data = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                lines = page.extract_text().split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()

                    # cari baris yang cocok dengan tanggal waktu
                    if re.match(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$', line):
                        waktu = line
                        deskripsi = ""
                        debit = kredit = saldo = 0.0
                        j = 1
                        while i + j < len(lines) and j <= 3:
                            next_line = lines[i + j].strip()
                            angka = re.findall(r'-?[\d.,]+', next_line)

                            if len(angka) >= 3:
                                deskripsi = re.sub(r'-?[\d.,]+', '', next_line).strip()
                                debit = parse_float(angka[-3])
                                kredit = parse_float(angka[-2])
                                saldo = parse_float(angka[-1])
                                break
                            else:
                                deskripsi += " " + next_line
                            j += 1
                        data.append([waktu, deskripsi.strip(), debit, kredit, saldo])
                        i += j
                    else:
                        i += 1
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses PDF: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna()

def convert_df_to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    buffer.seek(0)
    return buffer.read()

def main():
    st.set_page_config(page_title="Ekstraksi PDF Rekening Mandiri", layout="centered")
    st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF", type=["pdf"])
    if uploaded is not None:
        df = extract_transactions_from_pdf(uploaded)

        if df.empty:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"✅ Berhasil mengekstrak {len(df)} transaksi.")
            st.dataframe(df)

            excel = convert_df_to_excel(df)
            st.download_button("📥 Unduh Excel", data=excel,
                               file_name="Rekening_Mandiri.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
