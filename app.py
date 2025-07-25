import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import re

st.set_page_config(page_title="Ekstraksi PDF Rekening Mandiri ke Excel", layout="centered")

def extract_transactions_from_pdf(file):
    rows = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for i, line in enumerate(lines):
                # Deteksi format tanggal + waktu di awal baris
                match = re.match(r"(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2}) (.+)", line)
                if match:
                    tanggal = match.group(1)
                    jam = match.group(2)
                    deskripsi = match.group(3)
                    deskripsi_lengkap = deskripsi
                    # Tambahkan baris berikutnya kalau bagian dari deskripsi
                    j = i + 1
                    while j < len(lines) and not re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", lines[j]):
                        deskripsi_lengkap += " " + lines[j]
                        j += 1
                    # Ambil angka terakhir di deskripsi sebagai kemungkinan debit/kredit/saldo
                    angka = re.findall(r"[-]?\d{1,3}(?:\.\d{3})*,\d{2}", deskripsi_lengkap)
                    angka_float = [float(a.replace(".", "").replace(",", ".")) for a in angka]

                    # Normalisasi: debit, kredit, saldo — tergantung jumlah angka
                    debit = kredit = saldo = 0.0
                    if len(angka_float) >= 3:
                        debit, kredit, saldo = angka_float[-3:]
                    elif len(angka_float) == 2:
                        kredit, saldo = angka_float
                    elif len(angka_float) == 1:
                        saldo = angka_float[0]

                    rows.append({
                        "Waktu Transaksi": pd.to_datetime(f"{tanggal} {jam}", dayfirst=True, errors='coerce'),
                        "Deskripsi": deskripsi_lengkap.strip(),
                        "Debit": debit,
                        "Kredit": kredit,
                        "Saldo": saldo
                    })
    df = pd.DataFrame(rows)
    return df.dropna(subset=["Waktu Transaksi"])

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Transaksi")
    return output.getvalue()

def main():
    st.title("📄 Ekstraksi PDF Rekening Mandiri ke Excel")
    st.caption("Unggah file PDF")

    uploaded_file = st.file_uploader("Drag and drop file here", type="pdf")

    if uploaded_file:
        df = extract_transactions_from_pdf(uploaded_file)

        if df.empty:
            st.warning("⚠️ Tidak ada transaksi berhasil diekstrak.")
        else:
            st.success(f"✅ Berhasil mengekstrak {len(df)} transaksi.")
            st.dataframe(df)

            excel_bytes = convert_df_to_excel(df)
            st.download_button("📥 Unduh Excel", data=excel_bytes, file_name="Rekening_Mandiri.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
