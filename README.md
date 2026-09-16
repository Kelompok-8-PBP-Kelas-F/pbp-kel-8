# Thrift.io

## Deskripsi Aplikasi
**Thrift.io** adalah sebuah aplikasi web yang mengusung tema *slow fashion* dan *conscious shopping*. Aplikasi ini berfokus pada ekosistem *thrifting* (pasar barang bekas layak pakai) untuk mengurangi limbah fashion dan mempromosikan gaya hidup berkelanjutan. Selain berfungsi sebagai *marketplace* barang *preloved*, aplikasi ini juga menjadi pusat komunitas bagi para pecinta mode melalui fitur pencarian acara, berita terbaru, forum diskusi, hingga alat pengonsep pakaian (*outfit builder*).

## Arsitektur & Teknologi
Aplikasi ini dikembangkan menggunakan tumpukan teknologi berikut:
- **Backend:** Django (Python)
- **Frontend:** Vanilla CSS & Vanilla JavaScript
- **Database:** SQLite / PostgreSQL (Bawaan Django / Disesuaikan)

## Fitur Utama & Daftar Modul Rencana

1. **Modul Autentikasi & Profil Pengguna**
   - Registrasi, login, dan manajemen profil pengguna.
2. **Modul Preloved Items Marketplace**
   - CRUD (Create, Read, Update, Delete) daftar barang *preloved*.
   - Pencarian, filter kategori, dan sistem transaksi/keranjang belanja.
3. **Modul Fashion/Thrifting Event Near You**
   - Pemetaan dan daftar acara fashion (bazaar, pameran, *swap meet*) di sekitar pengguna.
4. **Modul Fashion News**
   - Agregasi dan kurasi artikel atau berita terbaru seputar *slow fashion* dan tren mode.
5. **Modul Fashion Forum**
   - Wadah diskusi komunitas untuk berbagi tips *styling*, perawatan baju, dan diskusi *sustainable fashion*.
6. **Modul Outfit Builder from Photos**
   - Fitur interaktif di mana pengguna dapat mengunggah foto pakaian mereka, menghapus latar belakangnya, dan memadupadankan (*mix and match*) pakaian di atas kanvas virtual.

## Public API
Untuk mendukung fungsionalitas fitur, proyek ini mengintegrasikan beberapa Public API:
- **OpenStreetMap API:** Digunakan pada modul *Fashion Event Near You* untuk menampilkan peta interaktif dan titik lokasi acara secara akurat.
- **Fashion/News API (misal: NewsAPI atau kustom):** Digunakan pada modul *Fashion News* untuk menarik data artikel dan berita mode terkini secara otomatis.
- **Poof.bg API (atau API background removal serupa):** Digunakan pada modul *Outfit Builder* untuk memproses foto pakaian yang diunggah pengguna, menghapus latar belakang gambar agar mudah disusun di kanvas.

## Peran Pengguna (User Roles)
Aplikasi ini mendukung beberapa tingkatan akses pengguna:
1. **Guest (Pengunjung Belum Login):** Dapat melihat artikel berita, daftar acara di peta, serta melihat-lihat katalog *marketplace* dan membaca forum diskusi publik.
2. **Registered User (Pembeli & Penjual):** Memiliki akses penuh untuk menjual barang *preloved*, membeli barang, berpartisipasi (membuat *thread*/komentar) di forum, menyimpan acara, dan menggunakan fitur *outfit builder*.
3. **Admin/Moderator:** Memiliki hak akses ke *dashboard* Django admin untuk mengelola pengguna, menyetujui/menghapus *listing* barang yang melanggar aturan, mengelola artikel berita, serta memoderasi forum.

##Anggota tim:

- **Luthfi Ahmad Fadhlan / 2506617203** 
- **Maulana Farrel Arvindra / 2506552802** 
- **Muhammad Nabil Hariri / 2506602302**
- **Marclay Ardell Taufiqurrachman Harahap / 2506621024**
- **Razan Alif Azhima / 2506632942** 
