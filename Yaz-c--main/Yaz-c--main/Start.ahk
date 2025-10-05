#Requires AutoHotkey v2.0
; --- AYARLAR ---
txtPath := A_ScriptDir "\metinim.txt"   ; Aynı klasördeki metin dosyası
SendMode "Event"                        ; Tuş taklidi için Event modu (gecikme destekler)
SetKeyDelay 20, 20                      ; Tuşlar arası ve basılı tutma süresi (ms)

; F9 -> "İnsan gibi" yaz (gerçekçi tempo, satır satır + Enter)
F9:: {
    try text := FileRead(txtPath, "UTF-8")  ; Türkçe karakterler için UTF-8
    catch {
        MsgBox "Dosya okunamadı: " txtPath
        return
    }
    for line in StrSplit(text, "`n", "`r") {
        ; Metni özel karakter çevrimi olmadan yazmak için Text modu:
        Send "{Text}" line
        ;Send "{CRTL+J}"
        ;Send, ^j
        ;^j::Send "^j"
        Send("^j")
        Sleep Random(15, 200)   ; satırlar arası rastgele bekleme (15-200ms)
    }
    ;Send(Enter)
}


; Ctrl+Esc -> Scripti kapat
^Esc:: ExitApp
