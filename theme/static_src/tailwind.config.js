/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        // Memindai folder root templates milik kita
        '../../templates/**/*.html',
        
        // Memindai template bawaan app (berjaga-jaga jika ada)
        '../templates/**/*.html',
        '../../**/templates/**/*.html',
    ],
    theme: {
        extend: {},
    },
    plugins: [
        /**
         * Plugin bawaan Tailwind yang sering dipakai.
         * Jika error karena plugin belum terinstall, kamu bisa menghapus atau
         * meng-comment baris plugin di bawah ini sementara waktu.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}