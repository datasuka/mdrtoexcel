def extract_transactions(file):
    rows = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            st.text_area("DEBUG - Isi PDF", text[:3000], height=250)
            lines = text.split('\n')
            current_block = []

            for line in lines:
                if re.match(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$', line.strip()):
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
            # Ambil tanggal dan waktu dari baris pertama
            waktu_line = block[0].strip()
            tanggal, waktu = waktu_line.split(" ")

            # Ambil baris angka dari blok terakhir yang mengandung 3 angka valid
            angka_line = next(
                (l for l in reversed(block) if len(re.findall(r'-?[\d.,]+', l)) >= 3),
                None
            )
            if not angka_line:
                continue

            angka = re.findall(r'-?[\d.,]+', angka_line)
            debit = parse_amount(angka[-3])
            kredit = parse_amount(angka[-2])
            saldo = parse_amount(angka[-1])

            # Gabungkan deskripsi dari seluruh baris selain waktu dan angka
            deskripsi_lines = [l.strip() for l in block[1:] if l.strip() != angka_line.strip()]
            deskripsi = ' '.join(deskripsi_lines)

            data.append([f"{tanggal} {waktu}", deskripsi, debit, kredit, saldo])
        except Exception as e:
            continue

    df = pd.DataFrame(data, columns=["Waktu Transaksi", "Deskripsi", "Debit", "Kredit", "Saldo"])
    df["Waktu Transaksi"] = pd.to_datetime(df["Waktu Transaksi"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna(subset=["Waktu Transaksi"])
