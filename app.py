import random
import numpy as np
from prettytable import PrettyTable
import plotly.graph_objects as go
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Fungsi untuk membuat grafik garis
def plot_line_chart(x, y, title, xaxis_title, yaxis_title):
    # Membuat diagram garis menggunakan Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Waktu'))
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
    )
    fig.show()

# Fungsi untuk menghitung parameter antrian
def hitung_antrian(waktu_kedatangan, waktu_pelayanan):
    try:
        # Menghitung laju kedatangan dan pelayanan
        laju_kedatangan = 1 / waktu_kedatangan
        laju_pelayanan = 1 / waktu_pelayanan
        
        # Pemanfaatan pelayan (ρ)
        pemanfaatan = laju_kedatangan / laju_pelayanan
        
        # Waktu rata-rata dalam sistem (W)
        W = 1 / (laju_pelayanan - laju_kedatangan)
        
        # Waktu rata-rata dalam antrian (Wq)
        Wq = laju_kedatangan / (laju_pelayanan * (laju_pelayanan - laju_kedatangan))
        
        # Mengembalikan hasil perhitungan
        return {
            'laju_kedatangan': laju_kedatangan,
            'laju_pelayanan': laju_pelayanan,
            'pemanfaatan': pemanfaatan,
            'W': W,
            'Wq': Wq
        }
    except ZeroDivisionError:
        return None  # Jika ada pembagian dengan nol

# Fungsi utama antrian
def antrian(num_of_cust, kedatangan, layanan):
    tiba = []
    labels = []
    for i in range(len(kedatangan)):
        tiba.append({
            "nama": f"Pasien {i + 1}",
            "waktu_kedatangan": kedatangan[i],
            "waktu_layanan": layanan[i],
        })
        labels.append(f"Nama {i+1}")

    mulai = []   
    lebar = []   
    tabel = PrettyTable([ 
        "Nama", "Waktu Kedatangan", "Waktu Layanan", "Waktu Mulai Layanan", 
        "Waktu Selesai Layanan", "Waktu Putar", "Waktu Tunggu", "Waktu Respon"
    ])
    
    waktu = 0  # Jam simulasi
    n = len(tiba)
    dieksekusi = 0
    sekarang = None
    antrian_menunggu = []
    proses_tereksekusi = set()
    waktu_sisa = { 
        p["nama"]: [p["waktu_layanan"], None, 0]  # Memastikan waktu selesai awalnya None
        for p in tiba
    }
    total_waktu_layanan = 0
    total_waktu_sibuk = 0

    while dieksekusi < n:
        for p in tiba:
            if p["waktu_kedatangan"] == waktu and p["nama"] not in proses_tereksekusi:
                antrian_menunggu.append(p)

                if (not sekarang) or (antrian_menunggu and waktu_sisa[p["nama"]][1] and 
                                       (waktu_sisa[p["nama"]][1] < waktu_sisa[sekarang["nama"]][1])):
                    if sekarang:
                        print(f"\nMeninggalkan {sekarang['nama']} dan Beralih ke proses {p['nama']} karena prioritas.\n")
                    sekarang = p

        if not sekarang and antrian_menunggu:
            sekarang = min(antrian_menunggu, key=lambda x: waktu_sisa[x["nama"]][1] if waktu_sisa[x["nama"]][1] is not None else float('inf'))

        if not sekarang and not antrian_menunggu:
            print(f"\nWaktu {waktu}: Server sedang tidak sibuk.\n")

        if sekarang:
            print(f"Waktu {waktu}: Menjalankan {sekarang['nama']}")

            if waktu_sisa[sekarang["nama"]][2] == 0:
                waktu_sisa[sekarang["nama"]][2] = waktu  # Waktu mulai layanan

            if waktu_sisa[sekarang["nama"]][0] > 0:
                waktu_sisa[sekarang["nama"]][0] -= 1
                total_waktu_layanan += 1
                total_waktu_sibuk += 1

            if waktu_sisa[sekarang["nama"]][0] <= 0:
                proses_tereksekusi.add(sekarang["nama"])
                waktu_sisa[sekarang["nama"]][1] = waktu  # Waktu selesai layanan
                antrian_menunggu = [p for p in antrian_menunggu if p["nama"] != sekarang["nama"]]

                waktu_putar = waktu_sisa[sekarang["nama"]][1] - sekarang["waktu_kedatangan"]
                waktu_tunggu = max(waktu_putar - sekarang["waktu_layanan"], 0)
                waktu_respon = waktu_sisa[sekarang["nama"]][2] - sekarang["waktu_kedatangan"]

                tiba[dieksekusi]["waktu_putar"] = waktu_putar
                tiba[dieksekusi]["waktu_tunggu"] = waktu_tunggu
                tiba[dieksekusi]["waktu_respon"] = waktu_respon
                
                tabel.add_row([
                    sekarang["nama"], sekarang["waktu_kedatangan"], sekarang["waktu_layanan"],
                    waktu_sisa[sekarang["nama"]][2], waktu_sisa[sekarang["nama"]][1],
                    waktu_putar, waktu_tunggu, waktu_respon
                ])
                lebar.append(waktu_putar)
                mulai.append(waktu_sisa[sekarang["nama"]][2])
                sekarang = None
                dieksekusi += 1

        waktu += 1

    # Menampilkan tabel hasil
    print(tabel)

    # Menghitung rata-rata waktu
    total_waktu_tunggu = sum([row[6] for row in tabel.rows])
    total_waktu_putar = sum([row[5] for row in tabel.rows])
    total_waktu_respon = sum([row[7] for row in tabel.rows])

    rata_rata_waktu_tunggu = total_waktu_tunggu / n
    rata_rata_waktu_putar = total_waktu_putar / n
    rata_rata_waktu_respon = total_waktu_respon / n

    print(f"\nRata-rata Waktu Tunggu: {rata_rata_waktu_tunggu:.2f}")
    print(f"Rata-rata Waktu Putar: {rata_rata_waktu_putar:.2f}")
    print(f"Rata-rata Waktu Respon: {rata_rata_waktu_respon:.2f}")

    # Menampilkan grafik garis untuk waktu tunggu dan waktu putar
    plot_line_chart([i for i in range(len(tiba))], [tiba[i]["waktu_tunggu"] for i in range(len(tiba))],
                   "Distribusi Waktu Tunggu", "Nomor Pasien", "Waktu Tunggu")
    plot_line_chart([i for i in range(len(tiba))], [tiba[i]["waktu_putar"] for i in range(len(tiba))],
                   "Distribusi Waktu Putar", "Nomor Pasien", "Waktu Putar")

# Halaman utama untuk menerima input
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            waktu_kedatangan = float(request.form["waktu_kedatangan"])
            waktu_pelayanan = float(request.form["waktu_pelayanan"])

            # Validasi input
            if waktu_kedatangan <= 0 or waktu_pelayanan <= 0:
                return render_template("index.html", error="Waktu kedatangan dan waktu pelayanan harus positif.")
            
            # Hitung hasil antrian
            hasil = hitung_antrian(waktu_kedatangan, waktu_pelayanan)
            if hasil:
                return render_template("result.html", hasil=hasil)
            else:
                return render_template("index.html", error="Perhitungan tidak valid, pastikan input benar.")
        except ValueError:
            return render_template("index.html", error="Masukkan angka yang valid.")
    return render_template("index.html")

# Halaman untuk menampilkan hasil perhitungan
@app.route("/hasil")
def hasil():
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
