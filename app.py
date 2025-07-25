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
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Cari baris tanggal & waktu
                if re.match(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$', line):
                    waktu = line
                    deskripsi = ""
                    debit = kredit = saldo = 0.0

                    # Cek 3 baris berikutnya
                    for j in range(1, 4):
                        if i + j < len(lines):
                            next_line = lines[i + j].strip()
                            nums = re.findall(r'-?[\d.,]+', next_line)

                            if len(nums) >= 3:
                                # Ambil deskripsi dan angka
                                deskripsi = re.sub(r'-?[\d.,]+', '', next_line).strip()
                                debit = parse_float(nums[-3])
                                kredit = parse_float(nums[-2])
                                saldo = parse_float(nums[-1])
                                break
                            else:
                                deskripsi += " " + next_line.strip()

                    data.append([waktu, deskripsi.strip(), debit, kredit, saldo])
                    i += j  # loncat ke bawah angka
                i += 1

    df = pd.DataFrame(data, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna()

def convert_df_to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return buffer.getvalue()

def main():
    st.set_page_config(page_title="Ekstraksi PDF Rekening Mandiri", layout="centered")
    st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")

    uploaded = st.file_uploader("Unggah file PDF", type=["pdf"])
    if uploaded:
        df = extract_transactions_from_pdf(uploaded)

        if df.empty:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"✅ {len(df)} transaksi berhasil diekstrak.")
            st.dataframe(df)

            excel = convert_df_to_excel(df)
            st.download_button("📥 Unduh Excel", data=excel,
                               file_name="Rekening_Mandiri.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
