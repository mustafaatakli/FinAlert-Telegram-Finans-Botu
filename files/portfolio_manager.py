from database import get_db, Portfolio
from scrapers import get_doviz_data, get_altin_data, get_borsa_data
from datetime import datetime


def format_price(price):
    """Fiyatı Türk Lirası formatında göster"""
    return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def add_portfolio_item(user_id, asset_type, asset_name, amount, purchase_price):
    """
    Portföye yeni varlık ekle
    
    Args:
        user_id: Kullanıcı ID'si
        asset_type: Varlık türü (doviz, altin, hisse)
        asset_name: Varlık adı (USD, gram, THYAO vb.)
        amount: Miktar
        purchase_price: Alış fiyatı
    
    Returns:
        bool: Başarılı ise True
    """
    db = get_db()
    
    try:
        portfolio_item = Portfolio(
            user_id=user_id,
            asset_type=asset_type,
            asset_name=asset_name,
            amount=amount,
            purchase_price=purchase_price,
            purchase_date=datetime.now()
        )
        
        db.add(portfolio_item)
        db.commit()
        db.close()
        
        return True
    
    except Exception as e:
        print(f"❌ Portföy ekleme hatası: {e}")
        db.close()
        return False


def get_user_portfolio(user_id):
    """
    Kullanıcının tüm portföyünü getir
    
    Returns:
        list: Portföy öğeleri listesi
    """
    db = get_db()
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    db.close()
    
    return portfolio


def calculate_portfolio_profit_loss(user_id):
    """
    Kullanıcının portföy kar/zararını hesapla
    
    Returns:
        dict: Detaylı kar/zarar bilgileri
    """
    portfolio = get_user_portfolio(user_id)
    
    if not portfolio:
        return None
    
    # Güncel fiyatları çek
    doviz_data = get_doviz_data()
    altin_data = get_altin_data()
    borsa_data = get_borsa_data()
    
    total_investment = 0  # Toplam yatırım
    total_current_value = 0  # Toplam güncel değer
    items_detail = []
    
    for item in portfolio:
        current_price = None
        
        # Güncel fiyatı al
        if item.asset_type == 'doviz':
            if item.asset_name in doviz_data:
                current_price = doviz_data[item.asset_name]['satis']
        
        elif item.asset_type == 'altin':
            if item.asset_name in altin_data:
                current_price = altin_data[item.asset_name]['satis']
        
        elif item.asset_type == 'hisse':
            if item.asset_name in borsa_data:
                current_price = borsa_data[item.asset_name]['deger']
        
        if current_price:
            # Hesaplamalar
            investment_value = item.amount * item.purchase_price
            current_value = item.amount * current_price
            profit_loss = current_value - investment_value
            profit_loss_percent = (profit_loss / investment_value) * 100 if investment_value > 0 else 0
            
            total_investment += investment_value
            total_current_value += current_value
            
            items_detail.append({
                'id': item.id,
                'asset_type': item.asset_type,
                'asset_name': item.asset_name,
                'amount': item.amount,
                'purchase_price': item.purchase_price,
                'current_price': current_price,
                'investment_value': investment_value,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
                'purchase_date': item.purchase_date
            })
    
    # Toplam kar/zarar
    total_profit_loss = total_current_value - total_investment
    total_profit_loss_percent = (total_profit_loss / total_investment) * 100 if total_investment > 0 else 0
    
    return {
        'total_investment': total_investment,
        'total_current_value': total_current_value,
        'total_profit_loss': total_profit_loss,
        'total_profit_loss_percent': total_profit_loss_percent,
        'items': items_detail
    }


def delete_portfolio_item(item_id):
    """
    Portföyden varlık sil
    
    Args:
        item_id: Silinecek öğenin ID'si
    
    Returns:
        bool: Başarılı ise True
    """
    db = get_db()
    
    try:
        item = db.query(Portfolio).filter(Portfolio.id == item_id).first()
        
        if item:
            db.delete(item)
            db.commit()
            db.close()
            return True
        
        db.close()
        return False
    
    except Exception as e:
        print(f"❌ Portföy silme hatası: {e}")
        db.close()
        return False


def format_portfolio_report(portfolio_data):
    """
    Portföy raporunu formatla
    
    Args:
        portfolio_data: calculate_portfolio_profit_loss() sonucu
    
    Returns:
        str: Formatlanmış rapor
    """
    if not portfolio_data or not portfolio_data['items']:
        return "💼 Portföyünüz boş.\n\n/menu komutunu kullanarak portföyünüze varlık ekleyebilirsiniz."
    
    report = "💼 *Portföy Raporu*\n\n"
    
    # Varlık türlerine göre grupla
    doviz_items = [item for item in portfolio_data['items'] if item['asset_type'] == 'doviz']
    altin_items = [item for item in portfolio_data['items'] if item['asset_type'] == 'altin']
    hisse_items = [item for item in portfolio_data['items'] if item['asset_type'] == 'hisse']
    
    # Dövizler
    if doviz_items:
        report += "💱 *Döviz*\n"
        for item in doviz_items:
            emoji = "📈" if item['profit_loss'] > 0 else "📉" if item['profit_loss'] < 0 else "➖"
            report += f"• *{item['asset_name']}* x {item['amount']:.2f}\n"
            report += f"  Alış: ₺{format_price(item['purchase_price'])}\n"
            report += f"  Güncel: ₺{format_price(item['current_price'])}\n"
            report += f"  K/Z: {emoji} ₺{format_price(item['profit_loss'])} (%{item['profit_loss_percent']:.2f})\n\n"
    
    # Altınlar
    if altin_items:
        report += "🏆 *Altın*\n"
        for item in altin_items:
            emoji = "📈" if item['profit_loss'] > 0 else "📉" if item['profit_loss'] < 0 else "➖"
            altin_names = {
                'gram': 'Gram', 'ceyrek': 'Çeyrek', 'yarim': 'Yarım',
                'tam': 'Tam', 'cumhuriyet': 'Cumhuriyet', 'ons': 'Ons'
            }
            name = altin_names.get(item['asset_name'], item['asset_name'])
            report += f"• *{name}* x {item['amount']:.2f}\n"
            report += f"  Alış: ₺{format_price(item['purchase_price'])}\n"
            report += f"  Güncel: ₺{format_price(item['current_price'])}\n"
            report += f"  K/Z: {emoji} ₺{format_price(item['profit_loss'])} (%{item['profit_loss_percent']:.2f})\n\n"
    
    # Hisseler
    if hisse_items:
        report += "📈 *Hisse Senetleri*\n"
        for item in hisse_items:
            emoji = "📈" if item['profit_loss'] > 0 else "📉" if item['profit_loss'] < 0 else "➖"
            report += f"• *{item['asset_name']}* x {item['amount']:.0f}\n"
            report += f"  Alış: ₺{format_price(item['purchase_price'])}\n"
            report += f"  Güncel: ₺{format_price(item['current_price'])}\n"
            report += f"  K/Z: {emoji} ₺{format_price(item['profit_loss'])} (%{item['profit_loss_percent']:.2f})\n\n"
    
    # Toplam özet
    total_emoji = "📈" if portfolio_data['total_profit_loss'] > 0 else "📉" if portfolio_data['total_profit_loss'] < 0 else "➖"
    
    report += "━━━━━━━━━━━━━━━\n"
    report += f"💰 *Toplam Yatırım:* ₺{format_price(portfolio_data['total_investment'])}\n"
    report += f"💎 *Güncel Değer:* ₺{format_price(portfolio_data['total_current_value'])}\n"
    report += f"{total_emoji} *Toplam K/Z:* ₺{format_price(portfolio_data['total_profit_loss'])} "
    report += f"(%{portfolio_data['total_profit_loss_percent']:.2f})\n\n"
    report += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    return report

