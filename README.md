.\python-3.13.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0 /log C:\Windows\Temp\python-install.log
py -m pip install -r requirements.txt
py .\main.py

# Birlestirilmis Otomasyon Araci

Bu proje, eski AutoHotkey senaryosu ile OpenCV tabanli ekran otomasyonunu tek bir Python uygulamasinda toplar. Artik AutoHotkey kurmaya gerek yok; tum isler `main.py` altinda toplanmistir.

## Ozellikler
- Coklu monitor destegiyle goruntuden sablon eslestirme ve otomatik tiklama
- `Folder_Type_A`, `Folder_Type_Y`, `Folder_Type_1`, `Folder_Type_2` klasorlerine eklediginiz gorseller dongu boyunca yeniden taranir
- Eslesen goruntu icin klasor kuralligina gore tiklama sonrasi tus (`Shift+A`, `y`, `1`, `2`) gonderilir
- F8 ile fare koordinat HUD'u, Ctrl+Shift+C ile koordinat kopyalama
- F9 ile `text.txt` icerigini satir satir, rastgele araliklarla ve `Ctrl+J` ile gonderme
- ESC ile guvenli cikis, tum kancalar temizlenir

## Dizin Yapisi
- `main.py` - birlesik otomasyon uygulamasi
- `requirements.txt` - gerekli Python paketleri
- `Folder_Type_A/` - eslesme sonrasi tikla ve `Shift+A` gonder
- `Folder_Type_Y/` - eslesme sonrasi tikla ve `y` gonder
- `Folder_Type_1/` - eslesme sonrasi tikla ve `1` gonder
- `Folder_Type_2/` - eslesme sonrasi tikla ve `2` gonder
- `text.txt` - F9 ile gonderilecek metin (UTF-8 olarak kaydedin)

Yeni goruntu eklemek icin ilgili klasore kopyalamaniz yeterli; kodu guncellemeniz gerekmez. Uygulama her dongude klasorleri yeniden tarar.

## Kurulum
1. Python 3.10+ (Tkinter dahil) ve pip kurulu olmali.
2. (Onerilir) Sanal ortam hazirlayin:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Gerekli paketleri kurun:
   ```powershell
   pip install -r requirements.txt
   ```

## Calistirma
```powershell
python main.py
```

Coklu monitor kullaniyorsaniz ekran goruntusu alma yetkisine, klavye ve fare kontrolu icin yonetici iznine ihtiyac duyabilirsiniz. Yetki eksikliginde `keyboard` veya `pyautogui` kutuphaneleri hata verebilir.

## Kisayollar
- **F8**: HUD ac/kapat (basili tut)
- **Ctrl+Shift+C**: Fare X,Y koordinatlarini panoya kopyala
- **F9**: `text.txt` icerigini yaz (satir aralarinda rastgele gecikme + `Ctrl+J`)
- **ESC**: Uygulamadan cik

## Klasor Davranisini Ozellestirme
`main.py` icindeki `FOLDER_CONFIG` sozlugu, klasor -> tus eslemesini tanimlar:
```python
FOLDER_CONFIG = {
    "Folder_Type_A": "shift+a",  # Tikla ve 'A' gonder
    "Folder_Type_Y": "y",        # Tikla ve 'y' gonder
    "Folder_Type_1": "1",        # Tikla ve '1' gonder
    "Folder_Type_2": "2",        # Tikla ve '2' gonder
}
```
- Baska klasorler eklemek veya farkli tuslar (or. `"ctrl+j"`, `"enter"`) gondermek icin bu sozlugu guncelleyin.
- Tus dizileri `keyboard.send()` formatiyla uyumlu olmalidir.

## Metin Gonderimi (F9)
- `text.txt` dosyasini UTF-8 olarak kaydedin.
- Her satir yazildiktan sonra `Ctrl+J` gonderilir.
- Komut devam ederken F9 tekrarina izin verilmez; is tamamlandiginda veya ESC ile cikinca tekrar calistirabilirsiniz.

## Ipucalari
- Goruntu eslesmesi icin ekran cozunurlugu ve DPI ile birebir yakalanmis sablonlar kullanin.
- Eslesme bulunamazsa esik degerini (`threshold`) `main.py` icinde dusurmayi deneyin.
- Yonetici olarak calistirmak, global kisayollarin sorunsuz yakalanmasina yardimci olur.




