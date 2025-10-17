import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent
import config
import re

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print(" yfinance yüklü değil. Yahoo Finance özellikleri çalışmayacak.")

ua = UserAgent()


def get_headers():
    """Random user agent ile header oluştur"""
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }


def safe_request(url, delay=True):
    """Güvenli HTTP isteği - Ban yememek için gecikmeli"""
    if delay:
        time.sleep(random.uniform(1, 3))
    else:
        # Anlık veri için kısa gecikme
        time.sleep(random.uniform(0.3, 0.8))
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response
    except Exception as e:
        print(f" İstek hatası ({url}): {e}")
        return None


def parse_price(text):
    """Fiyat textini float'a çevir"""
    if not text:
        return 0.0
    
    # Türkçe formatı temizle: 1.234,56 -> 1234.56
    text = str(text).strip()
    text = text.replace('.', '')
    text = text.replace(',', '.')
    text = re.sub(r'[^\d.]', '', text)
    
    try:
        return float(text)
    except:
        return 0.0


# ===== DÖVİZ MODÜLÜ =====
def get_doviz_data():
    """
    Döviz verilerini çek (USD, EUR, GBP vb.)
    ANLIK CANLI VERİ - Çoklu kaynak ile yedekli sistem
    Kaynak bilgisi de döndürülür
    """
    try:
        # ÖNCELİK 1: [link1 web sitesi adı]
        doviz_data = get_doviz_sabah()
        if doviz_data and len(doviz_data) > 0:
            doviz_data['_kaynak'] = 'link1'
            return doviz_data
        
        # ÖNCELİK 2: [link2 web sitesi adı]
        doviz_data = get_doviz_mynet()
        if doviz_data and len(doviz_data) > 0:
            doviz_data['_kaynak'] = 'link2'
            return doviz_data
        
        # ÖNCELİK 3: [link3 web sitesi adı]
        doviz_data = get_doviz_dovizcom_html()
        if doviz_data and len(doviz_data) > 0:
            doviz_data['_kaynak'] = 'link3'
            return doviz_data
        
        # ÖNCELİK 4: [link4 web sitesi adı]
        doviz_data = get_doviz_bigpara()
        if doviz_data and len(doviz_data) > 0:
            doviz_data['_kaynak'] = 'link4'
            return doviz_data
        
        # ÖNCELİK 5: [link5 web sitesi adı]
        doviz_data = get_doviz_exchangerate()
        if doviz_data and len(doviz_data) > 0:
            doviz_data['_kaynak'] = 'link5'
            return doviz_data
        
        # ÖNCELİK 6: [link6 web sitesi adı]
        doviz_data = get_doviz_dovizcom_api()
        if doviz_data and len(doviz_data) > 0:
            doviz_data['_kaynak'] = 'link6'
            return doviz_data
        
        # ÖNCELİK 7  [link7 web sitesi adı]
        doviz_data = get_doviz_tcmb()
        doviz_data['_kaynak'] = 'link7'
        return doviz_data
    
    except Exception as e:
        print(f" Döviz verisi çekme hatası: {e}")
        doviz_data = get_doviz_tcmb()
        doviz_data['_kaynak'] = 'linK7'
        return doviz_data


def get_doviz_tcmb():
    """
    link1 ad
    """
    try:
        url = "link1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            
            doviz_dict = {}
            
            # USD
            usd = soup.find('Currency', {'CurrencyCode': 'USD'})
            if usd:
                doviz_dict['USD'] = {
                    'alis': parse_price(usd.find('BanknoteBuying').text if usd.find('BanknoteBuying') else '0'),
                    'satis': parse_price(usd.find('BanknoteSelling').text if usd.find('BanknoteSelling') else '0'),
                    'degisim': 0.0
                }
            
            # EUR
            eur = soup.find('Currency', {'CurrencyCode': 'EUR'})
            if eur:
                doviz_dict['EUR'] = {
                    'alis': parse_price(eur.find('BanknoteBuying').text if eur.find('BanknoteBuying') else '0'),
                    'satis': parse_price(eur.find('BanknoteSelling').text if eur.find('BanknoteSelling') else '0'),
                    'degisim': 0.0
                }
            
            # GBP
            gbp = soup.find('Currency', {'CurrencyCode': 'GBP'})
            if gbp:
                doviz_dict['GBP'] = {
                    'alis': parse_price(gbp.find('BanknoteBuying').text if gbp.find('BanknoteBuying') else '0'),
                    'satis': parse_price(gbp.find('BanknoteSelling').text if gbp.find('BanknoteSelling') else '0'),
                    'degisim': 0.0
                }
            
            return doviz_dict
        
        return {}
    
    except Exception as e:
        print(f"linK1 verisi çekme hatası: {e}")
        return {}


def get_doviz_exchangerate():
    """
    link2 ad
    """
    try:
        doviz_dict = {}
        
        currencies = ['USD', 'EUR', 'GBP']
        
        for code in currencies:
            try:
                url = f"link2/{code}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    rate = data.get('rates', {}).get('TRY', 0)
                    
                    if rate > 0:
                        doviz_dict[code] = {
                            'alis': rate * 0.998,  # %0.2 spread
                            'satis': rate * 1.002,
                            'degisim': 0.0
                        }
            except:
                pass
        
        return doviz_dict
    
    except Exception as e:
        print(f" link2 API hatası: {e}")
        return {}


def get_doviz_mynet():
    """
    link3 ad
    """
    try:
        url = "link3"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        doviz_dict = {}
        

        table = soup.find('table')
        
        if not table:
            return {}
        
        rows = table.find_all('tr')
        
        # Döviz mapping
        doviz_mapping = {
            'USD': ['dolar', 'usd', 'amerikan doları', 'amerikan dolari'],
            'EUR': ['euro', 'eur', 'avrupa'],
            'GBP': ['sterlin', 'gbp', 'ingiliz sterlini', 'ingiliz', 'pound']
        }
        
        for row in rows:
            cells = row.find_all('td')
            
            # Tablo yapısı: İsim | İkon | Son | Alış | Satış | % | Tarih
            if len(cells) >= 5:
                try:
                    isim = cells[0].text.strip().lower()
                    
                    # Alış ve Satış sütunları (index 3 ve 4)
                    alis = parse_price(cells[3].text)
                    satis = parse_price(cells[4].text)
                    
                    # Sadece pozitif değerleri al
                    if alis <= 0 or satis <= 0:
                        continue
                    
                    # Döviz tipini belirle - daha spesifik kontrol
                    matched = False
                    
                    # USD kontrolü - Kanada ve Avustralya doları hariç
                    if ('dolar' in isim or 'usd' in isim) and 'USD' not in doviz_dict:
                        if 'kanada' not in isim and 'avustralya' not in isim:
                            doviz_dict['USD'] = {
                                'alis': alis,
                                'satis': satis,
                                'degisim': 0.0
                            }
                            matched = True
                    
                    # EUR kontrolü
                    if not matched and ('euro' in isim or 'eur' in isim) and 'EUR' not in doviz_dict:
                        doviz_dict['EUR'] = {
                            'alis': alis,
                            'satis': satis,
                            'degisim': 0.0
                        }
                        matched = True
                    
                    # GBP kontrolü
                    if not matched and ('sterlin' in isim or 'gbp' in isim or 'ingiliz' in isim) and 'GBP' not in doviz_dict:
                        doviz_dict['GBP'] = {
                            'alis': alis,
                            'satis': satis,
                            'degisim': 0.0
                        }
                        matched = True
                
                except Exception as e:
                    continue
        
        return doviz_dict
    
    except Exception as e:
        print(f" link3 Finans döviz hatası: {e}")
        return {}


def get_doviz_dovizcom_html():
    """
    link4 ad
    """
    try:
        url = "link4 ad"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        doviz_dict = {}
        

        # Her döviz için ayrı div/kart yapısı var
        
        # USD
        try:
            usd_div = soup.find('div', {'data-code': 'USD'}) or soup.find('span', string=lambda t: t and 'dolar' in t.lower() if t else False)
            if usd_div:
                parent = usd_div.find_parent('div', class_=['item', 'currency-item'])
                if parent:
                    alis_elem = parent.find('span', class_=['value', 'buy', 'alis'])
                    satis_elem = parent.find('span', class_=['value', 'sell', 'satis'])
                    
                    if alis_elem and satis_elem:
                        doviz_dict['USD'] = {
                            'alis': parse_price(alis_elem.text),
                            'satis': parse_price(satis_elem.text),
                            'degisim': 0.0
                        }
        except:
            pass
        
        # EUR
        try:
            eur_div = soup.find('div', {'data-code': 'EUR'}) or soup.find('span', string=lambda t: t and 'euro' in t.lower() if t else False)
            if eur_div:
                parent = eur_div.find_parent('div', class_=['item', 'currency-item'])
                if parent:
                    alis_elem = parent.find('span', class_=['value', 'buy', 'alis'])
                    satis_elem = parent.find('span', class_=['value', 'sell', 'satis'])
                    
                    if alis_elem and satis_elem:
                        doviz_dict['EUR'] = {
                            'alis': parse_price(alis_elem.text),
                            'satis': parse_price(satis_elem.text),
                            'degisim': 0.0
                        }
        except:
            pass
        
        # GBP
        try:
            gbp_div = soup.find('div', {'data-code': 'GBP'}) or soup.find('span', string=lambda t: t and 'sterlin' in t.lower() if t else False)
            if gbp_div:
                parent = gbp_div.find_parent('div', class_=['item', 'currency-item'])
                if parent:
                    alis_elem = parent.find('span', class_=['value', 'buy', 'alis'])
                    satis_elem = parent.find('span', class_=['value', 'sell', 'satis'])
                    
                    if alis_elem and satis_elem:
                        doviz_dict['GBP'] = {
                            'alis': parse_price(alis_elem.text),
                            'satis': parse_price(satis_elem.text),
                            'degisim': 0.0
                        }
        except:
            pass
        
        return doviz_dict
    
    except Exception as e:
        print(f" link4 HTML hatası: {e}")
        return {}


def get_doviz_sabah():
    """
    link5 ad
    """
    try:
        url = "link5"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        doviz_dict = {}
        
        #  tablosu - basit ve temiz yapı
        # Tablo yapısı: DÖVİZ | ALIŞ (TL) | SATIŞ (TL) | SAAT | FARK (%)
        table = soup.find('table')
        
        if not table:
            return {}
        
        rows = table.find_all('tr')
        
        # Döviz mapping - daha spesifik kontrol
        doviz_mapping = {
            'USD': ['dolar', 'usd'],
            'EUR': ['euro', 'eur'],
            'GBP': ['sterlin', 'gbp', 'ingiliz']
        }
        
        for row in rows:
            cells = row.find_all('td')
            
            # En az 3 sütun olmalı: İsim, Alış, Satış
            if len(cells) >= 3:
                try:
                    # İlk sütun: Döviz ismi (hem text hem de link içeriğini kontrol et)
                    # Link içindeki text'i de al
                    first_cell = cells[0]
                    link = first_cell.find('a')
                    
                    if link:
                        # Link varsa hem link text'ini hem de full text'i al
                        link_text = link.text.strip().lower()
                        full_text = first_cell.text.strip().lower()
                        isim = link_text + " " + full_text
                    else:
                        isim = first_cell.text.strip().lower()
                    
                    # İkinci sütun: Alış fiyatı
                    alis = parse_price(cells[1].text)
                    
                    # Üçüncü sütun: Satış fiyatı
                    satis = parse_price(cells[2].text)
                    
                    # Sadece pozitif değerleri al
                    if alis <= 0 or satis <= 0:
                        continue
                    
                    # Döviz tipini belirle - tam eşleşme kontrolü
                    for code, search_terms in doviz_mapping.items():
                        matched = False
                        for term in search_terms:
                            # Kelime sınırlarını kontrol et
                            # "dolar" arıyorsak sadece "dolar" veya "usd" kelimesini bul
                            # "kanada doları" gibi diğer para birimlerini atla
                            if code == 'USD' and ('dolar' in isim or 'usd' in isim):
                                # "kanada" veya "avustralya" içermiyorsa USD'dir
                                if 'kanada' not in isim and 'avustralya' not in isim:
                                    matched = True
                                    break
                            elif code == 'EUR' and ('euro' in isim or 'eur' in isim):
                                matched = True
                                break
                            elif code == 'GBP' and ('sterlin' in isim or 'gbp' in isim or 'ingiliz' in isim):
                                # "sterlin", "gbp" veya "ingiliz" içeriyorsa GBP'dir
                                matched = True
                                break
                        
                        if matched and code not in doviz_dict:  # Daha önce eklenmemişse
                            doviz_dict[code] = {
                                'alis': alis,
                                'satis': satis,
                                'degisim': 0.0
                            }
                            break
                
                except Exception as e:
                    continue
        
        return doviz_dict
    
    except Exception as e:
        print(f" link5 Finans döviz hatası: {e}")
        return {}


def get_doviz_bigpara():
    """
    link6 ad
    """
    try:
        url = "link6"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        doviz_dict = {}
        
        # link6'da veri çekme
        # USD
        try:
            usd_row = soup.find('tr', {'data-name': 'dolar'})
            if usd_row:
                cells = usd_row.find_all('td')
                if len(cells) >= 3:
                    doviz_dict['USD'] = {
                        'alis': parse_price(cells[1].text),
                        'satis': parse_price(cells[2].text),
                        'degisim': 0.0
                    }
        except:
            pass
        
        # EUR
        try:
            eur_row = soup.find('tr', {'data-name': 'euro'})
            if eur_row:
                cells = eur_row.find_all('td')
                if len(cells) >= 3:
                    doviz_dict['EUR'] = {
                        'alis': parse_price(cells[1].text),
                        'satis': parse_price(cells[2].text),
                        'degisim': 0.0
                    }
        except:
            pass
        
        # GBP - link "sterlin" olarak geçiyor
        try:
            gbp_row = soup.find('tr', {'data-name': 'sterlin'})
            if gbp_row:
                cells = gbp_row.find_all('td')
                if len(cells) >= 3:
                    doviz_dict['GBP'] = {
                        'alis': parse_price(cells[1].text),
                        'satis': parse_price(cells[2].text),
                        'degisim': 0.0
                    }
        except:
            pass
        
        return doviz_dict
    
    except Exception as e:
        print(f"link6 hatası: {e}")
        return {}


def get_doviz_dovizcom_api():
    """
    link7 JSON API - RESMİ API
    """
    try:
        url = "link7"
        response = requests.get(url, timeout=5)
        
        # link JSON API
        if response.status_code == 200:
            try:
                data = response.json()
                doviz_dict = {}
                
                # USD
                if 'USD' in data:
                    usd = data['USD']
                    doviz_dict['USD'] = {
                        'alis': parse_price(usd.get('buying', 0)),
                        'satis': parse_price(usd.get('selling', 0)),
                        'degisim': 0.0
                    }
                
                # EUR
                if 'EUR' in data:
                    eur = data['EUR']
                    doviz_dict['EUR'] = {
                        'alis': parse_price(eur.get('buying', 0)),
                        'satis': parse_price(eur.get('selling', 0)),
                        'degisim': 0.0
                    }
                
                # GBP
                if 'GBP' in data:
                    gbp = data['GBP']
                    doviz_dict['GBP'] = {
                        'alis': parse_price(gbp.get('buying', 0)),
                        'satis': parse_price(gbp.get('selling', 0)),
                        'degisim': 0.0
                    }
                
                return doviz_dict
            except:
                pass
        
        # API çalışmazsa HTML scraping
        url = "link7"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        doviz_dict = {}
        
        # Basit div yapısı
        for code in ['USD', 'EUR', 'GBP']:
            try:
                item = soup.find('div', {'data-code': code})
                if item:
                    values = item.find_all('span', class_='value')
                    if len(values) >= 2:
                        doviz_dict[code] = {
                            'alis': parse_price(values[0].text),
                            'satis': parse_price(values[1].text),
                            'degisim': 0.0
                        }
            except:
                pass
        
        return doviz_dict
    
    except Exception as e:
        print(f" link7 hatası: {e}")
        return {}


# ===== ALTIN MODÜLÜ =====
def get_altin_data():
    """
    Altın fiyatlarını çek - ANLIK CANLI VERİ
    Çoklu kaynak ile yedekli sistem
    Kaynak bilgisi de döndürülür
    """
    try:
        # ÖNCELİK 1: [link8 web sitesi adı]
        altin_data = get_altin_mynet()
        if altin_data and len(altin_data) > 0:
            altin_data['_kaynak'] = 'link8'
            return altin_data
        
        # ÖNCELİK 2: [link9 web sitesi adı]
        altin_data = get_altin_bigpara()
        if altin_data and len(altin_data) > 0:
            altin_data['_kaynak'] = 'link9'
            return altin_data
        
        # ÖNCELİK 3: [link10 web sitesi adı]
        altin_data = get_altin_trt()
        if altin_data and len(altin_data) > 0:
            altin_data['_kaynak'] = 'link10'
            return altin_data
        
        # ÖNCELİK 4: [link11 web sitesi adı]
        altin_data = get_altin_genelpara()
        if altin_data and len(altin_data) > 0:
            altin_data['_kaynak'] = 'link11'
            return altin_data
        
        # ÖNCELİK 5: [link12 web sitesi adı]
        altin_data = get_altin_collectapi()
        altin_data['_kaynak'] = 'link12'
        return altin_data
    
    except Exception as e:
        print(f" Altın verisi çekme hatası: {e}")
        return {'_kaynak': 'Hata'}


def get_altin_trt():
    """
    link8 ad
    """
    try:
        url = "link8"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        altin_dict = {}
        
        # link8 altın tablosu - modern HTML yapısı
        # Web sayfadaki tablo yapısını ara
        tables = soup.find_all(['table', 'div'], class_=lambda x: x and 'table' in str(x).lower())
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 3:
                    isim_cell = cells[0].text.strip().lower()
                    
                    # Altın tipini belirle
                    altin_key = None
                    if 'gram' in isim_cell and 'altın' in isim_cell or 'gram altin' in isim_cell:
                        altin_key = 'gram'
                    elif 'çeyrek' in isim_cell or 'ceyrek' in isim_cell:
                        altin_key = 'ceyrek'
                    elif 'yarım' in isim_cell or 'yarim' in isim_cell:
                        altin_key = 'yarim'
                    
                    if altin_key:
                        try:
                            alis = parse_price(cells[1].text)
                            satis = parse_price(cells[2].text)
                            
                            if alis > 0 and satis > 0:
                                altin_dict[altin_key] = {
                                    'alis': alis,
                                    'satis': satis,
                                }
                        except:
                            pass
        
        # Alternatif: Tüm text'i tara ve pattern match yap
        if not altin_dict:
            page_text = soup.get_text()
            
            # Basit örnek değerler (fallback)
            # link çalışmazsa diğer kaynaklara geçecek
            pass
        
        return altin_dict
    
    except Exception as e:
        print(f" link8 altın scraping hatası: {e}")
        return {}


def get_altin_bigpara():
    """
    link9 ad
    """
    try:
        url = "link9"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        altin_dict = {}
        
        # link altın için basit tablo
        altin_mapping = {
            'gram': ['gram-altin', 'gram altın'],
            'ceyrek': ['ceyrek-altin', 'çeyrek altın'],
            'yarim': ['yarim-altin', 'yarım altın'],
            'tam': ['tam-altin', 'tam altın'],
            'cumhuriyet': ['cumhuriyet-altini', 'cumhuriyet altını'],
            'ons': ['ons-altin', 'ons altın']
        }
        
        for altin_type, search_terms in altin_mapping.items():
            try:
                row = None
                for term in search_terms:
                    row = soup.find('tr', {'data-name': term})
                    if row:
                        break
                    # Alternatif arama
                    row = soup.find('a', string=lambda t: t and term in t.lower())
                    if row:
                        row = row.find_parent('tr')
                        break
                
                if row:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        altin_dict[altin_type] = {
                            'alis': parse_price(cells[1].text),
                            'satis': parse_price(cells[2].text),
                        }
            except:
                pass
        
        return altin_dict
    
    except Exception as e:
        print(f" link9 altın hatası: {e}")
        return {}


def get_altin_collectapi():
    """
    link10 ad
    """
    try:
        # Ücretsiz endpoint
        url = "link10"
        
        # API key gerektirmeez(public endpoint)
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
                altin_dict = {}
                
                if 'result' in data:
                    items = data['result']
                    
                    for item in items:
                        name = item.get('name', '').lower()
                        
                        if 'gram' in name:
                            altin_dict['gram'] = {
                                'alis': parse_price(item.get('buying', 0)),
                                'satis': parse_price(item.get('selling', 0)),
                            }
                        elif 'çeyrek' in name or 'ceyrek' in name:
                            altin_dict['ceyrek'] = {
                                'alis': parse_price(item.get('buying', 0)),
                                'satis': parse_price(item.get('selling', 0)),
                            }
                        elif 'yarım' in name or 'yarim' in name:
                            altin_dict['yarim'] = {
                                'alis': parse_price(item.get('buying', 0)),
                                'satis': parse_price(item.get('selling', 0)),
                            }
                        elif 'tam' in name:
                            altin_dict['tam'] = {
                                'alis': parse_price(item.get('buying', 0)),
                                'satis': parse_price(item.get('selling', 0)),
                            }
                
                return altin_dict
            except:
                pass
        
        return {}
    
    except Exception as e:
        print(f" link10 hatası: {e}")
        return {}


def get_altin_mynet():
    """
    link11 ad
    """
    try:
        url = "link11"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        altin_dict = {}
        

        table = soup.find('table')
        
        if not table:
            return {}
        
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            
            # 7 sütun olmalı: İsim(0) | İkon(1) | Son(2) | Alış(3) | Satış(4) | %(5) | Tarih(6)
            if len(cells) >= 5:
                try:
                    isim = cells[0].text.strip().lower()
                    alis = parse_price(cells[3].text)  # Alış sütunu
                    satis = parse_price(cells[4].text)  # Satış sütunu
                    
                    # Sadece pozitif değerleri al
                    if alis <= 0 or satis <= 0:
                        continue
                    
                    # Altın tipini belirle (Kapalı Çarşı olmayan)
                    if 'kapalı' in isim or 'kapali' in isim:
                        continue
                    
                    altin_key = None
                    if 'gram' in isim and 'altın' in isim:
                        altin_key = 'gram'
                    elif 'çeyrek' in isim or 'ceyrek' in isim:
                        altin_key = 'ceyrek'
                    elif 'yarım' in isim or 'yarim' in isim:
                        altin_key = 'yarim'
                    elif 'cumhuriyet' in isim:
                        altin_key = 'cumhuriyet'
                    elif 'tam' in isim:
                        altin_key = 'tam'
                    elif 'ons' in isim and 'tl' in isim:
                        altin_key = 'ons'
                    
                    if altin_key:
                        altin_dict[altin_key] = {
                            'alis': alis,
                            'satis': satis,
                        }
                
                except Exception as e:
                    pass
        
        return altin_dict
    
    except Exception as e:
        print(f" link11 altın scraping hatası: {e}")
        return {}


def get_altin_genelpara():
    """
    link12 ad
    """
    try:
        url = "link12"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            altin_dict = {
                'gram': {
                    'alis': parse_price(data.get('GA', {}).get('alis', 0)),
                    'satis': parse_price(data.get('GA', {}).get('satis', 0)),
                },
                'ceyrek': {
                    'alis': parse_price(data.get('C', {}).get('alis', 0)),
                    'satis': parse_price(data.get('C', {}).get('satis', 0)),
                },
                'yarim': {
                    'alis': parse_price(data.get('Y', {}).get('alis', 0)),
                    'satis': parse_price(data.get('Y', {}).get('satis', 0)),
                },
                'tam': {
                    'alis': parse_price(data.get('T', {}).get('alis', 0)),
                    'satis': parse_price(data.get('T', {}).get('satis', 0)),
                },
                'cumhuriyet': {
                    'alis': parse_price(data.get('C', {}).get('alis', 0)),
                    'satis': parse_price(data.get('C', {}).get('satis', 0)),
                },
                'ons': {
                    'alis': parse_price(data.get('ONS', {}).get('alis', 0)) if data.get('ONS') else 0,
                    'satis': parse_price(data.get('ONS', {}).get('satis', 0)) if data.get('ONS') else 0,
                }
            }
            
            return altin_dict
        
        return {}
    
    except Exception as e:
        print(f" link12 API hatası: {e}")
        return {}


# ===== BORSA MODÜLÜ =====
def get_borsa_data():
    """
    Borsa fiyatları için web scrabing & API servisleri
    """
    try:
        # ÖNCELİK 1: [link13 web sitesi adı](python kütüphanesi ile calisan)
        borsa_data = get_borsa_yahoo()
        if borsa_data and len(borsa_data) > 0:
            borsa_data['_kaynak'] = 'link13'
            return borsa_data
        
        # ÖNCELİK 2: [link14 web sitesi adı] - JSON
        borsa_data = get_borsa_genelpara()
        if borsa_data and len(borsa_data) > 0:
            borsa_data['_kaynak'] = 'link14'
            return borsa_data
        
        # ÖNCELİK 3: [link15 web sitesi adı]
        borsa_data = get_borsa_bigpara()
        if borsa_data and len(borsa_data) > 0:
            borsa_data['_kaynak'] = 'link15'
            return borsa_data
        
        # ÖNCELİK 4: [link16 web sitesi adı] - Alternatif
        borsa_data = get_borsa_foreks()
        borsa_data['_kaynak'] = 'link16'
        return borsa_data
    
    except Exception as e:
        print(f"Borsa verisi çekme hatası: {e}")
        borsa_data = get_borsa_genelpara()
        borsa_data['_kaynak'] = 'link15API'
        return borsa_data


def get_borsa_yahoo():
    """
    link13 ad
    """
    try:
        if not YFINANCE_AVAILABLE:
            return {}
        
        borsa_dict = {}
        

        try:
            xu100 = yf.Ticker("XU100.IS")
            data = xu100.history(period="1d")
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                prev_close = xu100.info.get('previousClose', current_price)
                
                change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                
                borsa_dict['XU100'] = {
                    'deger': float(current_price),
                    'degisim_yuzde': float(change_percent),
                }
        except Exception as e:
            print(f"⚠️ XU100 link13 hatası: {e}")
        
        # Popüler hisseler - .IS uzantısı Borsa Istanbul için
        hisseler = {
            'THYAO': 'THYAO.IS',
            'GARAN': 'GARAN.IS',
            'AKBNK': 'AKBNK.IS',
            'EREGL': 'EREGL.IS',
            'SAHOL': 'SAHOL.IS',
            'TUPRS': 'TUPRS.IS',
            'PETKM': 'PETKM.IS',
            'SISE': 'SISE.IS'
        }
        
        for kod, ticker in hisseler.items():
            try:
                stock = yf.Ticker(ticker)
                data = stock.history(period="1d")
                
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    prev_close = stock.info.get('previousClose', current_price)
                    
                    change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                    
                    borsa_dict[kod] = {
                        'deger': float(current_price),
                        'degisim_yuzde': float(change_percent),
                    }
            except:
                pass
        
        return borsa_dict
    
    except Exception as e:
        print(f" link13 hatası: {e}")
        return {}


def get_borsa_foreks():
    """
    link14 ad
    """
    try:
        url = "link14"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        borsa_dict = {}
        
        # BIST 100
        try:
            bist_row = soup.find('tr', {'data-code': 'XU100'}) or \
                       soup.find('a', string=lambda t: t and 'BIST 100' in t)
            
            if bist_row:
                cells = bist_row.find_all('td') if bist_row.name == 'tr' else bist_row.find_next('tr').find_all('td')
                
                if len(cells) >= 2:
                    borsa_dict['XU100'] = {
                        'deger': parse_price(cells[1].text if len(cells) > 1 else cells[0].text),
                        'degisim_yuzde': parse_price(cells[2].text) if len(cells) > 2 else 0.0,
                    }
        except:
            pass
        
        # Popüler hisseler - basit tablo
        populer_hisseler = ['THYAO', 'GARAN', 'AKBNK', 'EREGL', 'SAHOL', 'TUPRS']
        
        for hisse in populer_hisseler:
            try:
                row = soup.find('tr', {'data-code': hisse}) or \
                      soup.find('a', string=hisse)
                
                if row:
                    cells = row.find_all('td') if row.name == 'tr' else row.find_next('tr').find_all('td')
                    
                    if len(cells) >= 2:
                        borsa_dict[hisse] = {
                            'deger': parse_price(cells[1].text),
                            'degisim_yuzde': parse_price(cells[2].text) if len(cells) > 2 else 0.0,
                        }
            except:
                pass
        
        return borsa_dict
    
    except Exception as e:
        print(f"link14 scraping hatası: {e}")
        return {}


def get_borsa_bigpara():
    """
    link15 ad
    """
    try:
        url = "link15"
        response = safe_request(url, delay=False)
        
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        borsa_dict = {}
        
        # BIST 100 - basit tablo satırı
        try:
            bist_row = soup.find('tr', {'data-code': 'XU100'})
            
            if bist_row:
                cells = bist_row.find_all('td')
                
                if len(cells) >= 3:
                    borsa_dict['XU100'] = {
                        'deger': parse_price(cells[1].text),
                        'degisim_yuzde': parse_price(cells[2].text),
                    }
        except:
            pass
        
        # Popüler hisseler - aynı basit yapı
        populer_hisseler = ['THYAO', 'GARAN', 'AKBNK', 'EREGL', 'SAHOL', 'TUPRS', 'PETKM', 'SISE']
        
        for hisse in populer_hisseler:
            try:
                row = soup.find('tr', {'data-code': hisse})
                
                if row:
                    cells = row.find_all('td')
                    
                    if len(cells) >= 3:
                        borsa_dict[hisse] = {
                            'deger': parse_price(cells[1].text),
                            'degisim_yuzde': parse_price(cells[2].text),
                        }
            except:
                pass
        
        return borsa_dict
    
    except Exception as e:
        print(f" link15 borsa scraping hatası: {e}")
        return {}


def get_borsa_genelpara():
    """
    link16 ad
    """
    try:
        url = "link16"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            borsa_dict = {
                'XU100': {
                    'deger': parse_price(data.get('XU100', {}).get('d', 0)),
                    'degisim_yuzde': parse_price(data.get('XU100', {}).get('dd', 0)),
                }
            }
            
            # Popüler hisseler
            populer_hisseler = ['THYAO', 'GARAN', 'AKBNK', 'EREGL', 'SAHOL', 'TUPRS', 'PETKM', 'SISE']
            
            for hisse in populer_hisseler:
                if hisse in data:
                    borsa_dict[hisse] = {
                        'deger': parse_price(data.get(hisse, {}).get('d', 0)),
                        'degisim_yuzde': parse_price(data.get(hisse, {}).get('dd', 0)),
                    }
            
            return borsa_dict
        
        return {}
    
    except Exception as e:
        print(f" link16 API hatası: {e}")
        return {}


# Test fonksiyonu
if __name__ == '__main__':
    print("Döviz verileri test ediliyor...")
    doviz = get_doviz_data()
    print(doviz)
    
    print("\n Altın verileri test ediliyor...")
    altin = get_altin_data()
    print(altin)
    
    print("\n Borsa verileri test ediliyor...")
    borsa = get_borsa_data()
    print(borsa)

