# 📄 PRODUCT REQUIREMENTS DOCUMENT (PRD)

**Nama Proyek:** Sistem Manajemen Perpustakaan (Library Management System)  
**Tumpukan Teknologi (Tech Stack):** FastAPI (Backend), React (Frontend), PostgreSQL (Database), Docker (Deployment)  
**Durasi Proyek:** 4 Minggu  
**Tim:** 4 Anggota Mahasiswa  

---

## 1. Tujuan Proyek
Menggantikan sistem manajemen perpustakaan berbasis *spreadsheet* manual yang rentan kesalahan dengan aplikasi digital terpusat. Sistem ini memudahkan mahasiswa mencari dan meminjam buku, serta membantu pustakawan mengelola katalog, menyetujui peminjaman, dan melacak keterlambatan.

## 2. Pengguna & Peran (`peran`)
1. **`mahasiswa`**: Dapat mencari katalog buku, mengajukan peminjaman, dan melihat batas waktu pengembalian.
2. **`pustakawan`**: Dapat mengelola katalog buku, menyetujui/menolak peminjaman, memantau buku terlambat, dan melihat laporan dasbor.

## 3. Kebutuhan Sistem (System Requirements)

### Kebutuhan Fungsional (Functional Requirements)
* **F01**: Pengguna dapat mendaftar (`registrasi`) dengan `email`, `kata_sandi`, dan `peran` (mahasiswa/pustakawan).
* **F02**: Pengguna dapat masuk (`masuk`) menggunakan autentikasi berbasis JWT.
* **F03**: Mahasiswa dapat mencari katalog buku berdasarkan `judul`, `penulis`, atau `isbn`.
* **F04**: Mahasiswa dapat mengajukan peminjaman untuk buku yang tersedia (maksimal 5 buku sekaligus).
* **F05**: Pustakawan dapat menyetujui atau menolak pengajuan peminjaman mahasiswa.
* **F06**: Sistem melacak tanggal tenggat pengembalian (14 hari tanpa perpanjangan) dan menandai buku yang terlambat serta menghitung denda (Rp 1.000/hari).
* **F07**: Pustakawan dapat menambah, mengedit, dan menghapus buku dari katalog.
* **F08**: Notifikasi keterlambatan dikirimkan secara otomatis via email menggunakan layanan pihak ketiga (Brevo API).

### Kebutuhan Non-Fungsional (Non-Functional Requirements)
* **NF01**: Seluruh respons API harus selesai di bawah 2 detik dalam beban normal.
* **NF02**: `kata_sandi` di-hash menggunakan **bcrypt**; sesi menggunakan **JWT** dengan masa berlaku 1 jam.
* **NF03**: Antarmuka (*frontend*) React harus responsif pada ukuran layar 375px ke atas.

---

## 4. Model Data (Skema Database PostgreSQL)

*Catatan: Semua nama tabel dan kolom menggunakan Bahasa Indonesia.*

**Tipe Data Kustom (ENUM):**
* `PERAN_PENGGUNA`: `('mahasiswa', 'pustakawan')`
* `KONDISI_BUKU`: `('bagus', 'rusak_ringan', 'rusak_berat')`
* `STATUS_SALINAN`: `('tersedia', 'dipesan', 'dipinjam')`
* `STATUS_PEMINJAMAN`: `('menunggu_persetujuan', 'siap_diambil', 'dipinjam', 'dibatalkan', 'dikembalikan', 'ditolak')`

### 1. Tabel `pengguna`
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `id` | UUID (PK) | ID unik pengguna |
| `nama` | VARCHAR(150) | Nama lengkap |
| `email` | VARCHAR(100) | Email institusi (Unik) |
| `kata_sandi` | VARCHAR(255) | Hash Bcrypt |
| `peran` | PERAN_PENGGUNA| `mahasiswa` atau `pustakawan` |
| `is_diblokir` | BOOLEAN | Default: `FALSE`. `TRUE` jika ada keterlambatan. |

### 2. Tabel `buku` (Master Data)
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `id` | UUID (PK) | ID Master Katalog |
| `judul` | VARCHAR(255) | Judul buku |
| `penulis` | VARCHAR(255) | Penulis buku |
| `isbn` | VARCHAR(20) | ISBN (Unik) |
| `kategori` | VARCHAR(100) | Kategori/Genre |
| `tahun_terbit`| INTEGER | Tahun publikasi |

### 3. Tabel `salinan_buku` (Inventaris Fisik)
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `id` | UUID (PK) | ID unik fisik/Barcode eksemplar |
| `id_buku` | UUID (FK) | Relasi ke tabel `buku` |
| `lokasi_rak` | VARCHAR(50) | Posisi rak (misal: 'A-1') |
| `kondisi` | KONDISI_BUKU | Default: `'bagus'` |
| `status_ketersediaan`| STATUS_SALINAN| Default: `'tersedia'` |

### 4. Tabel `peminjaman` (Transaksi)
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `id` | UUID (PK) | ID Transaksi |
| `id_pengguna` | UUID (FK) | Relasi ke `pengguna` |
| `id_salinan_buku`| UUID (FK) | Relasi ke `salinan_buku` fisik |
| `tanggal_pengajuan`| TIMESTAMP | Waktu saat diajukan |
| `tanggal_siap_ambil`| TIMESTAMP | Pemicu batas ambil 2x24 jam |
| `tanggal_pinjam` | TIMESTAMP | Waktu buku diserahkan |
| `tanggal_tenggat` | TIMESTAMP | `tanggal_pinjam` + 14 hari |
| `tanggal_kembali` | TIMESTAMP | Waktu buku dikembalikan fisik |
| `status_peminjaman`| STATUS_PEMINJAMAN| Status pelacakan saat ini |
| `total_denda` | INTEGER | Akumulasi Rp 1.000/hari terlambat |

---

## 5. Alur Kerja (Workflows)

**A. Alur Autentikasi**
1. Pengguna memanggil `/api/autentikasi/registrasi` dengan `email`, `kata_sandi`, `nama`, `peran`.
2. Pengguna memanggil `/api/autentikasi/masuk` dengan `email` dan `kata_sandi`. Sistem mengembalikan token JWT.

**B. Alur Peminjaman**
1. Mahasiswa memilih buku dan mengajukan peminjaman. Sistem memastikan mahasiswa memiliki `< 5` pinjaman aktif dan `is_diblokir = FALSE`.
2. Transaksi masuk dengan status `menunggu_persetujuan`.
3. Pustakawan meninjau dasbor. Jika ditolak, status menjadi `ditolak`.
4. Jika disetujui, status menjadi `siap_diambil`. *Timer* 2x24 jam dimulai.
5. Jika lewat 2x24 jam mahasiswa tidak datang, status menjadi `dibatalkan`.
6. Jika mahasiswa mengambil buku, pustakawan mengubah status menjadi `dipinjam`. *Timer* peminjaman 14 hari dimulai.

**C. Alur Pengembalian & Denda**
1. Mahasiswa mengembalikan buku. Sistem mengecek `tanggal_kembali` vs `tanggal_tenggat`.
2. Jika terlambat, `pengguna.is_diblokir` otomatis menjadi `TRUE`, email peringatan (Brevo) terkirim, dan `total_denda` terhitung (Rp 1.000 x jumlah hari terlambat).
3. Mahasiswa membayar denda tunai kepada Pustakawan. Pustakawan mengeklik tombol "Denda Lunas" pada sistem.
4. Status `peminjaman` berubah menjadi `dikembalikan`, dan `pengguna.is_diblokir` dikembalikan menjadi `FALSE`.

---

## 6. Kriteria Penerimaan & Langkah Verifikasi

| Fitur / Modul | Kriteria Penerimaan (Acceptance Criteria) | Langkah Verifikasi (Verification Steps) |
| :--- | :--- | :--- |
| **Otentikasi** | Kata sandi di-hash; API mengembalikan JWT valid 1 jam. | 1. Registrasi akun, periksa DB pastikan `kata_sandi` tidak berupa teks biasa (*plaintext*).<br>2. Coba akses *endpoint* yang dilindungi setelah 61 menit; pastikan akses ditolak (401 Unauthorized). |
| **Batas Pinjaman** | Menolak pengajuan jika mahasiswa memiliki 5 buku dengan status aktif atau jika `is_diblokir = TRUE`. | 1. Login sebagai mahasiswa, pinjam 5 buku, pastikan yang ke-6 gagal.<br>2. Set `is_diblokir = TRUE` di DB, pastikan pengajuan pertama sekalipun langsung gagal. |
| **Persetujuan** | Pustakawan dapat mengubah status menjadi `siap_diambil` atau `ditolak`. | 1. Gunakan token pustakawan untuk menerima/menolak, pastikan DB terupdate dan `status_ketersediaan` salinan ikut sinkron. |
| **Keterlambatan** | Jika lewat 14 hari, `is_diblokir` menjadi `TRUE`, email dikirim, dan denda terhitung otomatis. | 1. Buat peminjaman tiruan, majukan *clock server* 16 hari.<br>2. Pastikan denda tercatat Rp 2.000, pengguna terblokir, dan log email Brevo memunculkan status *Sent*. |
| **Kinerja API** | Maksimal waktu respons 2 detik. | 1. Gunakan alat seperti Postman/Artillery untuk mengetes batas beban normal. Cek *response time* di bawah 2000ms. |

---

## 7. Draft Arsitektur API (FastAPI)

Semua *endpoint* diawali dengan `/api`:

**Autentikasi:**
* `POST /autentikasi/registrasi`
* `POST /autentikasi/masuk`

**Katalog Buku:**
* `GET /buku` *(Bisa filter dengan `?kata_kunci=`, `?kategori=`)*
* `POST /buku` *(Khusus Pustakawan: Tambah master buku)*
* `POST /buku/{id_buku}/salinan` *(Khusus Pustakawan: Tambah fisik buku)*

**Peminjaman:**
* `POST /peminjaman/ajukan` *(Mahasiswa: Ajukan pinjam)*
* `PUT /peminjaman/{id_peminjaman}/persetujuan` *(Pustakawan: Setujui/Tolak)*
* `PUT /peminjaman/{id_peminjaman}/serahkan` *(Pustakawan: Ubah ke `dipinjam` saat fisik diserahkan)*
* `PUT /peminjaman/{id_peminjaman}/kembalikan` *(Pustakawan: Proses kembali dan kalkulasi denda)*
* `PUT /peminjaman/{id_peminjaman}/lunasi_denda` *(Pustakawan: Angkat status blokir)*