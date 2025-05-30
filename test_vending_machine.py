import unittest 

from vending_machine import (
    VendingMachine,
    STATE_IDLE, STATE_ACCEPTING_MONEY, STATE_READY_TO_SELECT,
    STATE_OUT_OF_STOCK_SELECTED, STATE_INSUFFICIENT_FUNDS_FOR_SELECTION,
    ACCEPTED_COINS
)

# Konfigurasi item awal standar untuk semua tes
DEFAULT_INITIAL_ITEMS_CONFIG = [
    {'id': 1, 'name': 'Teh Kotak', 'price': 3000, 'stock': 2},
    {'id': 2, 'name': 'Kopi Susu', 'price': 4000, 'stock': 1},
    {'id': 3, 'name': 'Air Mineral', 'price': 2000, 'stock': 0} # Stok habis
]

class TestVendingMachineBVA(unittest.TestCase):
    def setUp(self):
        """Dipanggil sebelum setiap metode tes."""
        self.vm = VendingMachine(DEFAULT_INITIAL_ITEMS_CONFIG)
        self.vm.reset_machine() # Pastikan mesin bersih untuk setiap tes

    def test_bva_insert_coin_valid_boundaries(self):
        print("\n menjalankan test_bva_insert_coin_valid_boundaries")
        # Koin valid terkecil
        self.assertTrue(self.vm.insert_coin(500))
        self.assertEqual(self.vm.get_current_balance(), 500)
        # Koin valid lain
        self.vm.reset_machine()
        self.assertTrue(self.vm.insert_coin(1000))
        self.assertEqual(self.vm.get_current_balance(), 1000)
        # Koin valid terbesar
        self.vm.reset_machine()
        self.assertTrue(self.vm.insert_coin(2000))
        self.assertEqual(self.vm.get_current_balance(), 2000)
        print(" selesai test_bva_insert_coin_valid_boundaries")


    def test_bva_insert_coin_invalid_values(self):
        print("\n menjalankan test_bva_insert_coin_invalid_values")
        # Di bawah batas terendah
        self.assertFalse(self.vm.insert_coin(100))
        self.assertEqual(self.vm.get_current_balance(), 0)
        # Di antara koin valid
        self.assertFalse(self.vm.insert_coin(700))
        self.assertEqual(self.vm.get_current_balance(), 0)
        # Di atas batas tertinggi
        self.assertFalse(self.vm.insert_coin(2500))
        self.assertEqual(self.vm.get_current_balance(), 0)
        print(" selesai test_bva_insert_coin_invalid_values")

    def test_bva_select_item_id_boundaries_and_invalid(self):
        print("\n menjalankan test_bva_select_item_id_boundaries_and_invalid")
        self.vm.insert_coin(2000)
        self.vm.insert_coin(2000) # Saldo 4000, STATE_READY_TO_SELECT

        # ID 0 (di bawah batas, tidak valid format)
        self.assertEqual(self.vm.select_item(0), "invalid_item_id_format")
        self.assertEqual(self.vm.get_current_state(), STATE_READY_TO_SELECT)

        # ID -1 (tidak valid format)
        self.assertEqual(self.vm.select_item(-1), "invalid_item_id_format")
        self.assertEqual(self.vm.get_current_state(), STATE_READY_TO_SELECT)

        # ID valid batas bawah (misal item 1 ada)
        # (Item 1: Teh Kotak, 3000, stok 2)
        # Hasilnya akan "dispensed_Teh Kotak_change_1000"
        self.assertTrue("dispensed_Teh Kotak" in self.vm.select_item(1))
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE) # Kembali ke IDLE setelah transaksi
        self.assertEqual(self.vm.get_item_stock(1), 1) # Stok berkurang

        # ID valid batas atas (misal item 2 ada, setelah reset saldo)
        self.vm.reset_machine()
        self.vm.insert_coin(2000); self.vm.insert_coin(2000) # Saldo 4000
        # (Item 2: Kopi Susu, 4000, stok 1)
        self.assertTrue("dispensed_Kopi Susu" in self.vm.select_item(2))
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE)
        self.assertEqual(self.vm.get_item_stock(2), 0)

        # ID tidak ada dalam daftar (misal ID 4, jika max ID di config adalah 3)
        self.vm.reset_machine()
        self.vm.insert_coin(2000)
        self.assertEqual(self.vm.select_item(4), "invalid_item_id_not_found")
        self.assertEqual(self.vm.get_current_state(), STATE_ACCEPTING_MONEY) # atau READY jika saldo cukup utk item lain
        print(" selesai test_bva_select_item_id_boundaries_and_invalid")


class TestVendingMachineSTT(unittest.TestCase):
    def setUp(self):
        self.vm = VendingMachine(DEFAULT_INITIAL_ITEMS_CONFIG)
        self.vm.reset_machine()

    def test_stt_successful_purchase_with_change(self):
        print("\n menjalankan test_stt_successful_purchase_with_change (STT_01)")
        # State Awal: IDLE
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE)

        # Event: insert_coin(2000)
        self.vm.insert_coin(2000)
        # State Antara: ACCEPTING_MONEY (karena 2000 < harga item termurah yg ada stok)
        # Teh Kotak (ID 1) harga 3000, stok 2. Kopi Susu (ID 2) harga 4000, stok 1.
        self.assertEqual(self.vm.get_current_state(), STATE_ACCEPTING_MONEY)

        # Event: insert_coin(2000) -> Saldo 4000
        self.vm.insert_coin(2000)
        # State Antara: READY_TO_SELECT
        self.assertEqual(self.vm.get_current_state(), STATE_READY_TO_SELECT)

        # Event: select_item(1) (Teh Kotak @3000)
        result = self.vm.select_item(1)
        self.assertTrue("dispensed_Teh Kotak" in result)
        self.assertTrue("change_1000" in result)
        # State Akhir: IDLE (setelah dispensing & returning change)
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE)
        self.assertEqual(self.vm.get_item_stock(1), 1) # Stok berkurang
        self.assertEqual(self.vm.get_current_balance(), 0) # Saldo habis setelah kembalian
        print(" selesai test_stt_successful_purchase_with_change")

    def test_stt_insufficient_funds_then_add_coin_and_purchase(self):
        print("\n menjalankan test_stt_insufficient_funds_then_add_coin_and_purchase (STT_02)")
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE)

        self.vm.insert_coin(1000) # Saldo 1000
        self.assertEqual(self.vm.get_current_state(), STATE_ACCEPTING_MONEY)

        # Coba pilih item 1 (Teh Kotak @3000) - uang kurang
        self.assertEqual(self.vm.select_item(1), "insufficient_funds")
        self.assertEqual(self.vm.get_current_state(), STATE_INSUFFICIENT_FUNDS_FOR_SELECTION)
        self.assertEqual(self.vm.get_current_balance(), 1000) # Saldo tetap

        # Masukkan koin lagi
        self.vm.insert_coin(2000) # Saldo jadi 3000
        self.assertEqual(self.vm.get_current_state(), STATE_READY_TO_SELECT)

        # Pilih item 1 lagi - sekarang berhasil
        result = self.vm.select_item(1)
        self.assertTrue("dispensed_Teh Kotak" in result)
        self.assertTrue("change_0" in result) # Kembalian 0
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE)
        self.assertEqual(self.vm.get_item_stock(1), 1)
        print(" selesai test_stt_insufficient_funds_then_add_coin_and_purchase")

    def test_stt_select_out_of_stock_then_select_available(self):
        print("\n menjalankan test_stt_select_out_of_stock_then_select_available (STT_03)")
        self.vm.insert_coin(2000)
        self.vm.insert_coin(2000) # Saldo 4000, State: READY_TO_SELECT
        self.assertEqual(self.vm.get_current_state(), STATE_READY_TO_SELECT)

        # Pilih item 3 (Air Mineral, stok 0)
        self.assertEqual(self.vm.select_item(3), "out_of_stock")
        self.assertEqual(self.vm.get_current_state(), STATE_OUT_OF_STOCK_SELECTED)
        self.assertEqual(self.vm.get_current_balance(), 4000) # Saldo tetap

        # Pilih item 1 (Teh Kotak, stok ada)
        result = self.vm.select_item(1)
        self.assertTrue("dispensed_Teh Kotak" in result)
        self.assertTrue("change_1000" in result)
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE)
        self.assertEqual(self.vm.get_item_stock(1), 1)
        print(" selesai test_stt_select_out_of_stock_then_select_available")

    def test_stt_cancel_transaction_with_balance(self):
        print("\n menjalankan test_stt_cancel_transaction_with_balance (STT_04)")
        self.vm.insert_coin(2000) # Saldo 2000
        self.assertEqual(self.vm.get_current_state(), STATE_ACCEPTING_MONEY) # Asumsi item termurah > 2000 atau ini jadi READY

        result = self.vm.cancel_transaction()
        self.assertEqual(result, "cancelled_returned_2000")
        self.assertEqual(self.vm.get_current_state(), STATE_IDLE)
        self.assertEqual(self.vm.get_current_balance(), 0)
        print(" selesai test_stt_cancel_transaction_with_balance")

if __name__ == '__main__':
    unittest.main(verbosity=2) # verbosity=2 untuk output yang lebih detail