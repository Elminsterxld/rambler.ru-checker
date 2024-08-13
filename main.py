import imaplib
import email
from email.header import decode_header
from datetime import datetime
import socks
import socket
import ssl
import time

PROXY_HOST = 'ipv4.eclipseproxy.com'  # Proxy addr
PROXY_PORT = 2222  # Port
PROXY_TYPE = socks.SOCKS5  # (SOCKS5, SOCKS4, HTTP)
PROXY_USER = 'eclipse_Elminsterxld'
PROXY_PASS = 'KXfOs1gMI1VWGMW8ma4W'

socks.set_default_proxy(PROXY_TYPE, PROXY_HOST, PROXY_PORT, True, PROXY_USER, PROXY_PASS)
socket.socket = socks.socksocket

IMAP_SERVER = 'imap.rambler.ru'
RETRY_LIMIT = 3
RETRY_DELAY = 5

def read_credentials(filename):
    with open(filename, 'r') as file:
        return [line.strip().split(':') for line in file]

def write_credentials(filename, credentials):
    with open(filename, 'w') as file:
        for cred in credentials:
            file.write(f"{cred[0]}:{cred[1]}\n")

def remove_credential(filename, email_user, email_pass):
    credentials = read_credentials(filename)
    credentials = [cred for cred in credentials if cred[0] != email_user or cred[1] != email_pass]
    write_credentials(filename, credentials)

def log_error(email_user, email_pass, error_message):
    with open('hatalı.txt', 'a') as f:
        f.write(f"{email_user}:{email_pass}:{error_message}\n")

def log_no_mail(email_user, email_pass):
    try:
        with open('boşmail.txt', 'a') as f:
            f.write(f"{email_user}:{email_pass}\n")
        print(f"Boş e-posta bilgileri kaydedildi: {email_user}:{email_pass}")
    except Exception as e:
        print(f"Boş e-posta bilgilerini kaydetme hatası: {e}")

def configure_proxy():
    socks.set_default_proxy(PROXY_TYPE, PROXY_HOST, PROXY_PORT, True, PROXY_USER, PROXY_PASS)
    socket.socket = socks.socksocket

def check_oldest_email(email_user, email_pass):
    retry_count = 0
    while retry_count < RETRY_LIMIT:
        try:
            configure_proxy()

            print("Bağlantı kuruluyor...")
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(email_user, email_pass)
            print("Giriş yapıldı.")

            mail.select('inbox')
            print("Inbox seçildi.")

            status, messages = mail.search(None, 'FROM "noreply@discord.com"')
            print(f"Arama sonuçları: {status}")

            email_ids = messages[0].split()
            print(f"Email ID'leri: {email_ids}")
            
            if email_ids:
                print(f"Yeni e-posta var! Hesap: {email_user}")
                
                oldest_date = None
                oldest_email_id = None
                
                for num in email_ids:
                    status, data = mail.fetch(num, '(RFC822)')
                    print(f"Mesaj alındı: {status}")
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            date_str = msg.get('Date')
                            if date_str:
                                try:
                                    date = email.utils.parsedate_tz(date_str)
                                    if date:
                                        date = datetime.fromtimestamp(email.utils.mktime_tz(date))
                                        print(f"İşlenen Tarih: {date}")
                                        
                                        if oldest_date is None or date < oldest_date:
                                            oldest_date = date
                                            oldest_email_id = num
                                except Exception as e:
                                    print(f"Tarih işleme hatası: {e}")
                
                if oldest_email_id:
                    status, data = mail.fetch(oldest_email_id, '(RFC822)')
                    print(f"En eski e-posta alındı: {status}")
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            subject, encoding = decode_header(msg['Subject'])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else 'utf-8')
                            
                            formatted_date = oldest_date.strftime('%Y-%m-%d %H:%M:%S')
                            
                            with open('results.txt', 'a') as f:
                                f.write(f"{email_user}:{email_pass}:{formatted_date}\n")
                            
                            print(f"Sonuç dosyaya yazıldı: {email_user}:{email_pass}:{formatted_date}")
                    
                    mail.logout()
                    return True 

                else:
                    print("Yeni e-posta yok.")
                    log_no_mail(email_user, email_pass)
                    mail.logout()
                    return True  
            else:
                print("noreply@discord.com adresinden gelen e-posta bulunamadı.")
                log_no_mail(email_user, email_pass)
                mail.logout()
                return True  
            
        except (socks.ProxyConnectionError, imaplib.IMAP4.error, ssl.SSLError) as e:
            retry_count += 1
            print(f"Bağlantı hatası ({retry_count}/{RETRY_LIMIT}): {e}")
            if retry_count < RETRY_LIMIT:
                print(f"{RETRY_DELAY} saniye sonra tekrar deneniyor...")
                time.sleep(RETRY_DELAY)
            else:
                log_error(email_user, email_pass, str(e))
                print(f"Bir hata oluştu: {e}. Hesap atlanıyor.")
                return False  

if __name__ == "__main__":
    credentials = read_credentials('mails.txt')

    for email_user, email_pass in credentials:
        if check_oldest_email(email_user, email_pass):
            remove_credential('mails.txt', email_user, email_pass)
