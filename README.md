# Birleştirilmiş Otomasyon Aracı

Bu proje, eski AutoHotkey senaryosu ile OpenCV tabanlı ekran otomasyonunu tek bir Python uygulamasında toplar. Artık AutoHotkey kurmaya gerek yok; tüm işler `main.py` altında toplanmıştır.

## Özellikler
- Çoklu monitör desteğiyle görsel eşleştirme ve tıklama
- `Folder_Type_A` ve `Folder_Type_Y` klasörlerine eklediğiniz görseller otomatik taranır
- Eşleşen görsel için istenen tuş otomatik gönderilir (varsayılan: `Folder_Type_Y` -> `y`)
- F8 ile fare koordinat HUD'u, Ctrl+Shift+C ile koordinat kopyalama
- F9 ile `metinim.txt` içeriğini satır satır, rastgele aralıklarla ve `Ctrl+J` ile gönderme
- ESC ile güvenli çıkış, tüm kancalar temizlenir

## Dizin Yapısı
- `main.py` – birleşik otomasyon uygulaması
- `requirements.txt` – gerekli Python paketleri
- `Folder_Type_A/` – görsel bulunduğunda **yalnızca tıklama** yapılır
- `Folder_Type_Y/` – görsel bulunduğunda tıklama + `'y'` tuşu gönderilir
- `metinim.txt` – F9 ile gönderilecek metin (UTF-8 kaydedin)

Yeni görsel eklemek için ilgili klasöre kopyalamanız yeterli; kodu güncellemeniz gerekmez. Uygulama her döngüde klasörleri yeniden tarar.

## Kurulum
1. Python 3.10+ (Tkinter dahil) ve pip kurulu olmalı.
2. (Önerilir) Sanal ortam hazırlayın:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Gerekli paketleri kurun:
   ```powershell
   pip install -r requirements.txt
   ```

## Çalıştırma
```powershell
python main.py
```

Çoklu monitör kullanıyorsanız ekran görüntüsü alma yetkisine, klavye ve fare kontrolü için yönetici iznine ihtiyaç duyabilirsiniz. Yetki eksikliğinde `keyboard` veya `pyautogui` kütüphaneleri hata verebilir.

## Kısayollar
- **F8**: HUD aç/kapat (basılı tut)
- **Ctrl+Shift+C**: Fare X,Y koordinatlarını panoya kopyala
- **F9**: `metinim.txt` içeriğini yaz (satır aralarında rastgele gecikme + `Ctrl+J`)
- **ESC**: Uygulamadan çık

## Klasör Davranışını Özelleştirme
`main.py` içindeki `FOLDER_CONFIG` sözlüğü, klasör -> tuş eşlemesini tanımlar:
```python
FOLDER_CONFIG = {
    "Folder_Type_A": None,      # Yalnızca tıkla
    "Folder_Type_Y": "y",      # Tıkla ve 'y' gönder
}
```
- Başka klasörler eklemek veya farklı tuşlar (ör. `"ctrl+j"`, `"enter"`) göndermek için bu sözlüğü güncelleyin.
- Tuş dizileri `keyboard.send()` formatıyla uyumlu olmalıdır.

## Metin Gönderimi (F9)
- `metinim.txt` dosyasını UTF-8 olarak kaydedin.
- Her satır yazıldıktan sonra `Ctrl+J` gönderilir.
- Komut devam ederken F9 tekrarına izin verilmez; iş tamamlandığında veya ESC ile çıkınca tekrar çalıştırabilirsiniz.

## İpuçları
- Görsel eşleşmesi için ekran çözünürlüğü ve DPI ile birebir yakalanmış şablonlar kullanın.
- Eşleşme bulunamazsa eşik değerini (`threshold`) `main.py` içinde düşürmeyi deneyin.
- Yönetici olarak çalıştırmak, global kısayolların sorunsuz yakalanmasına yardımcı olur.

