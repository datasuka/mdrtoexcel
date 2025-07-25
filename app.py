import streamlit as st
import pandas as pd
from io import BytesIO
import pdfplumber
import re

def extract_transactions_from_pdf(pdf_file):
    transactions = []
    with pdfplumber.open(pdf_file) as pdf:
        buffer = []
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            for line in lines:
                if re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", line):
                    if buffer:
                        txn = process_transaction(buffer)
                        if txn: transactions.append(txn)
                        buffer = []
                buffer.append(line.strip())
            if buffer:
                txn = process_transaction(buffer)
                if txn: transactions.append(txn)
                buffer = []
    df = pd.DataFrame(transactions, columns=["Tanggal", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], format="%d/%m/%Y", errors='coerce')
    return df.dropna(subset=["Tanggal"])

def process_transaction(lines):
    try:
        tanggal = lines[0][:10]
        angka_line = next((l for l in lines if l.startswith('-')), '')
        if not angka_line:
            return None
        parts = angka_line.strip().split()
        if len(parts) >= 4:
            debit = float(parts[1].replace(',', '').replace('.', '', parts[1].count('.')-1))
            kredit = float(parts[2].replace(',', '').replace('.', '', parts[2].count('.')-1))
            saldo = float(parts[3].replace(',', '').replace('.', '', parts[3].count('.')-1))
        else:
            return None
        deskripsi = ' '.join(lines[1:lines.index(angka_line)]).replace('  ', ' ')
        return [tanggal, deskripsi, debit, kredit, saldo]
    except:
        return None

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')
    return output.getvalue()

def main():
    st.title("Ekstrak Rekening Mandiri ke Excel")
    st.write("Unggah file PDF rekening Mandiri (format multi-baris per transaksi).")

    uploaded_file = st.file_uploader("Pilih file PDF rekening", type="pdf")
    if uploaded_file:
        df = extract_transactions_from_pdf(uploaded_file)
        st.dataframe(df, use_container_width=True)

        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="Unduh Excel",
            data=excel_data,
            file_name="Rekening_Mandiri.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
