# Simpan isi aplikasi Streamlit yang sudah diperbarui ke dalam file app.py

app_py_content = """
import streamlit as st
import pandas as pd
from io import BytesIO
import pdfplumber

def extract_transactions_from_pdf(pdf_file):
    transactions = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\\n')
            for i, line in enumerate(lines):
                if line[:10].count('/') == 2:  # Format tanggal: dd/mm/yyyy
                    parts = line.split()
                    try:
                        tanggal = parts[0]
                        saldo = float(parts[-1].replace(',', '').replace('.', '', parts[-1].count('.')-1))
                        kredit = float(parts[-2].replace(',', '').replace('.', '', parts[-2].count('.')-1)) if parts[-2] != '0.00' else 0.0
                        debit = float(parts[-3].replace(',', '').replace('.', '', parts[-3].count('.')-1)) if parts[-3] != '0.00' else 0.0
                        deskripsi = ' '.join(parts[1:-3])
                        transactions.append([tanggal, deskripsi, debit, kredit, saldo])
                    except:
                        continue
    df = pd.DataFrame(transactions, columns=["Tanggal", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], format="%d/%m/%Y", errors='coerce')
    return df

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title("Konversi Rekening Mandiri ke Excel")
    st.write("Unggah file PDF rekening koran Mandiri, dan sistem akan mengubahnya menjadi Excel.")

    uploaded_file = st.file_uploader("Pilih file PDF rekening koran", type="pdf")
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
"""

with open("/mnt/data/app.py", "w", encoding="utf-8") as f:
    f.write(app_py_content)

"/mnt/data/app.py"
