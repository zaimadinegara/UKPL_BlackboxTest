STATE_IDLE = "IDLE"
STATE_ACCEPTING_MONEY = "ACCEPTING_MONEY"
STATE_READY_TO_SELECT = "READY_TO_SELECT"
STATE_PROCESSING_SELECTION = "PROCESSING_SELECTION"
STATE_DISPENSING_ITEM = "DISPENSING_ITEM"
STATE_RETURNING_CHANGE = "RETURNING_CHANGE"
STATE_OUT_OF_STOCK_SELECTED = "OUT_OF_STOCK_SELECTED"
STATE_INSUFFICIENT_FUNDS_FOR_SELECTION = "INSUFFICIENT_FUNDS_FOR_SELECTION"

# Konstanta untuk Koin yang Diterima
ACCEPTED_COINS = [500, 1000, 2000]

class VendingMachine:
    def __init__(self, items):
        """
        Inisialisasi Vending Machine.
        :param items: List of dictionaries, setiap dictionary berisi 'id', 'name', 'price', 'stock'.
                      Contoh: [{'id': 1, 'name': 'Teh Botol', 'price': 3000, 'stock': 5}, ...]
        """
        self.items = {item['id']: item.copy() for item in items} # Gunakan .copy() agar item asli tidak termodifikasi
        self.initial_items_config = [item.copy() for item in items] # Simpan konfigurasi awal untuk reset
        self.current_balance = 0
        self.current_state = STATE_IDLE
        self.messages = []

    def _log_message(self, message):
        self.messages.append(message)
        # print(message) # Opsi: bisa langsung print atau gunakan logging library nanti

    def display_items(self):
        log_msgs = ["--- Daftar Minuman ---"]
        if not self.items:
            log_msgs.append("Mesin tidak memiliki item saat ini.")
        else:
            available_items_exist = False
            for item_id, item in self.items.items():
                if item['stock'] > 0:
                    log_msgs.append(f"{item['id']}. {item['name']} - Rp{item['price']} (Stok: {item['stock']})")
                    available_items_exist = True
            if not available_items_exist:
                log_msgs.append("Semua minuman habis.")
        log_msgs.append("----------------------")
        
        for msg in log_msgs:
            self._log_message(msg)
        return "\n".join(log_msgs)


    def insert_coin(self, coin_value):
        self._log_message(f"Mencoba memasukkan koin: Rp{coin_value}")
        if self.current_state not in [STATE_IDLE, STATE_ACCEPTING_MONEY, STATE_READY_TO_SELECT, STATE_OUT_OF_STOCK_SELECTED, STATE_INSUFFICIENT_FUNDS_FOR_SELECTION]:
            self._log_message(f"Tidak dapat memasukkan koin saat state: {self.current_state}")
            return False

        if coin_value not in ACCEPTED_COINS:
            self._log_message(f"Koin Rp{coin_value} tidak diterima. Hanya menerima: {ACCEPTED_COINS}")
            return False

        self.current_balance += coin_value
        self._log_message(f"Koin Rp{coin_value} diterima. Saldo saat ini: Rp{self.current_balance}")

        if self.current_balance > 0:
            can_buy_something = any(self.current_balance >= item['price'] for item in self.items.values() if item['stock'] > 0)
            if can_buy_something:
                self.current_state = STATE_READY_TO_SELECT
            else:
                self.current_state = STATE_ACCEPTING_MONEY
        return True

    def select_item(self, item_id):
        self._log_message(f"Mencoba memilih item ID: {item_id}")
        original_state_before_selection_attempt = self.current_state

        if self.current_state not in [STATE_READY_TO_SELECT, STATE_ACCEPTING_MONEY, STATE_OUT_OF_STOCK_SELECTED, STATE_INSUFFICIENT_FUNDS_FOR_SELECTION]:
            self._log_message(f"Tidak dapat memilih item saat state: {self.current_state}. Harap masukkan koin dulu atau batalkan transaksi.")
            return "selection_error_wrong_state"
        
        # BVA point: item_id validity (numerik dan dalam rentang)
        if not isinstance(item_id, int) or item_id <= 0 : # Anggap ID harus positif integer
             self._log_message(f"Item ID {item_id} tidak valid (harus integer positif).")
             return "invalid_item_id_format"

        if item_id not in self.items:
            self._log_message(f"Item ID {item_id} tidak ada dalam daftar produk.")
            # Tidak mengubah state utama dari error sebelumnya, biarkan pengguna mencoba lagi atau cancel
            return "invalid_item_id_not_found"

        selected_item = self.items[item_id]
        # self.current_state = STATE_PROCESSING_SELECTION # State ini bisa diabaikan jika prosesnya instan
        self._log_message(f"Memproses pilihan: {selected_item['name']}")

        if selected_item['stock'] <= 0:
            self._log_message(f"Maaf, {selected_item['name']} habis.")
            self.current_state = STATE_OUT_OF_STOCK_SELECTED
            return "out_of_stock"

        if self.current_balance < selected_item['price']:
            self._log_message(f"Maaf, saldo Anda (Rp{self.current_balance}) tidak cukup untuk {selected_item['name']} (Rp{selected_item['price']}).")
            self.current_state = STATE_INSUFFICIENT_FUNDS_FOR_SELECTION
            return "insufficient_funds"

        # Proses berhasil
        self.current_state = STATE_DISPENSING_ITEM
        self._log_message(f"Mengeluarkan {selected_item['name']}...")
        self.items[item_id]['stock'] -= 1
        self.current_balance -= selected_item['price']
        dispensed_item_name = selected_item['name']

        change_returned_amount = 0
        if self.current_balance > 0:
            change_returned_amount = self._return_internal_change()
        else:
            self._log_message("Tidak ada kembalian.")
            self.current_state = STATE_IDLE
            self._log_message("Transaksi selesai. Mesin kembali ke IDLE.")
        
        return f"dispensed_{dispensed_item_name}_change_{change_returned_amount}"

    def _return_internal_change(self):
        # Fungsi helper internal untuk mengelola state saat kembalian
        if self.current_balance > 0:
            self.current_state = STATE_RETURNING_CHANGE
            self._log_message(f"Mengembalikan kembalian: Rp{self.current_balance}")
            change_to_return = self.current_balance
            self.current_balance = 0
            self.current_state = STATE_IDLE # Langsung IDLE setelah kembalian
            self._log_message("Transaksi selesai (dengan kembalian). Mesin kembali ke IDLE.")
            return change_to_return
        return 0
        
    def cancel_transaction(self):
        self._log_message("Transaksi dibatalkan oleh pengguna.")
        if self.current_state == STATE_DISPENSING_ITEM or self.current_state == STATE_RETURNING_CHANGE:
            self._log_message("Tidak bisa membatalkan saat item/kembalian sedang diproses.")
            return "cancel_error_busy"

        returned_money = 0
        if self.current_balance > 0:
            self._log_message(f"Mengembalikan semua saldo: Rp{self.current_balance}")
            returned_money = self.current_balance
            self.current_balance = 0
        else:
            self._log_message("Tidak ada saldo untuk dikembalikan.")
        
        self.current_state = STATE_IDLE
        self._log_message("Mesin kembali ke IDLE setelah pembatalan.")
        return f"cancelled_returned_{returned_money}"

    def get_current_state(self):
        return self.current_state

    def get_current_balance(self):
        return self.current_balance

    def get_item_stock(self, item_id):
        if item_id in self.items:
            return self.items[item_id]['stock']
        return None
    
    def get_all_messages(self):
        return list(self.messages) # Kembalikan salinan

    def clear_messages(self):
        self.messages = []

    def reset_machine(self):
        """ Reset mesin ke kondisi awal dengan konfigurasi item awal. """
        # Buat salinan baru dari konfigurasi item awal
        self.items = {item['id']: item.copy() for item in self.initial_items_config}
        self.current_balance = 0
        self.current_state = STATE_IDLE
        self.clear_messages()
        self._log_message("Mesin direset ke kondisi awal.")

# --- Contoh Penggunaan Aplikasi Sederhana (bisa dijalankan langsung dari file ini) ---
if __name__ == "__main__":
    # Konfigurasi awal item
    default_initial_items = [
        {'id': 1, 'name': 'Teh Kotak', 'price': 3000, 'stock': 2},
        {'id': 2, 'name': 'Kopi Susu', 'price': 4000, 'stock': 1},
        {'id': 3, 'name': 'Air Mineral', 'price': 2000, 'stock': 0} # Stok habis
    ]

    vm = VendingMachine(default_initial_items)

    def print_vm_status(vending_machine):
        print(f"Saldo: Rp{vending_machine.get_current_balance()}, State: {vending_machine.get_current_state()}")
        # Cetak pesan terakhir untuk ringkasan aksi
        if vending_machine.messages:
            print(f"Log Terakhir: {vending_machine.messages[-1]}")
        print("-" * 20)

    print("\n--- SIMULASI PENGGUNAAN VENDING MACHINE ---")
    
    print("Menampilkan Item Awal:")
    print(vm.display_items())
    print_vm_status(vm)

    print("Skenario 1: Pembelian Sukses dengan Kembalian")
    vm.insert_coin(2000)
    print_vm_status(vm)
    vm.insert_coin(2000) # Saldo: 4000
    print_vm_status(vm)
    vm.select_item(1)     # Pilih Teh Kotak (3000)
    print_vm_status(vm)
    print(f"Sisa stok Teh Kotak: {vm.get_item_stock(1)}")
    
    print("\nSkenario 2: Uang Kurang")
    vm.reset_machine() # Reset untuk skenario baru
    print(vm.display_items())
    vm.insert_coin(1000) # Saldo: 1000
    print_vm_status(vm)
    vm.select_item(1)     # Pilih Teh Kotak (3000) -> INSUFFICIENT_FUNDS_FOR_SELECTION
    print_vm_status(vm)
    
    print("\nSkenario 3: Item Habis")
    vm.reset_machine()
    vm.insert_coin(2000) # Saldo: 2000
    print_vm_status(vm)
    vm.select_item(3)     # Pilih Air Mineral (stok 0) -> OUT_OF_STOCK_SELECTED
    print_vm_status(vm)

    print("\nSkenario 4: Koin Tidak Diterima")
    vm.insert_coin(100)   # Koin tidak diterima
    print_vm_status(vm)

    print("\nSkenario 5: Pembatalan")
    vm.reset_machine()
    vm.insert_coin(2000) # Saldo: 2000
    print_vm_status(vm)
    vm.cancel_transaction()
    print_vm_status(vm)

    print("\n--- Log Pesan Seluruh Simulasi (jika perlu) ---")
    # for msg in vm.get_all_messages(): # Jika ingin melihat semua log dari vm yang terakhir digunakan
    #     print(f"- {msg}")