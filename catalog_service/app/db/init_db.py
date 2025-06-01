# catalog_service/app/db/init_db.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.database import engine, async_session, Base
from db.models import Product, Category, Seller

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Теперь проверим и заполним данные
    async with async_session() as session:
        existing = (await session.execute(select(Category))).scalars().first()
        if existing:
            print("БД уже содержит данные, пропускаем заполнение.")
            return

        # Добавляем категории
        laptops = Category(name="Ноутбуки")
        monitors = Category(name="Мониторы")
        mice = Category(name="Мыши")
        keyboards = Category(name="Клавиатуры")
        headphones = Category(name="Наушники")
        components = Category(name="Комплектующие")
        session.add_all([laptops, monitors, mice, keyboards, headphones, components])
        await session.flush()

        # Добавляем продавцов
        seller1 = Seller(name="TechShop", description="Поставщик техники")
        seller2 = Seller(name="CompStore", description="Магазин компьютеров")
        seller3 = Seller(name="ElectroMarket", description="Электроника и гаджеты")
        seller4 = Seller(name="GamerZone", description="Игровые устройства")
        seller5 = Seller(name="OfficeTech", description="Офисная техника")
        seller6 = Seller(name="PremiumDevices", description="Премиум техника")
        seller7 = Seller(name="BudgetTech", description="Бюджетные решения")
        seller8 = Seller(name="ProEquipment", description="Профессиональное оборудование")
        seller9 = Seller(name="DigitalWorld", description="Цифровые технологии")
        seller10 = Seller(name="AllForPC", description="Все для компьютеров")
        
        session.add_all([seller1, seller2, seller3, seller4, seller5, 
                        seller6, seller7, seller8, seller9, seller10])
        await session.flush()

        # Добавляем товары (200 штук)
        products = [
            # Ноутбуки (50 товаров)
            Product(name="ASUS VivoBook 15", description="Универсальный ноутбук с процессором Intel Core i5", price=54000.0, stock=10, active=True, category_id=laptops.id, seller_id=seller1.id),
            Product(name="HP Pavilion 14", description="Ноутбук с SSD накопителем 512GB", price=62000.0, stock=8, active=True, category_id=laptops.id, seller_id=seller3.id),
            Product(name="Acer Nitro 5", description="Игровой ноутбук с GTX 1650", price=78000.0, stock=6, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Lenovo IdeaPad 3", description="Бюджетный ноутбук для офиса", price=45000.0, stock=12, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="MSI GF63 Thin", description="Тонкий игровой ноутбук", price=85000.0, stock=5, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Dell XPS 13", description="Премиальный ультрабук", price=112000.0, stock=4, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="Apple MacBook Air M1", description="Ноутбук на процессоре Apple Silicon", price=95000.0, stock=7, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="ASUS ROG Strix G15", description="Игровой ноутбук с RTX 3060", price=125000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Microsoft Surface Laptop 4", description="Ультрабук с сенсорным экраном", price=105000.0, stock=4, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="Gigabyte AORUS 15P", description="Игровой ноутбук с экраном 240Hz", price=135000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Huawei MateBook D15", description="Ультрабук с тонкими рамками", price=68000.0, stock=6, active=True, category_id=laptops.id, seller_id=seller3.id),
            Product(name="Lenovo ThinkPad X1 Carbon", description="Бизнес-ноутбук премиум класса", price=120000.0, stock=5, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Razer Blade 15", description="Игровой ноутбук с OLED экраном", price=180000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="ASUS ZenBook 14", description="Компактный ультрабук", price=88000.0, stock=7, active=True, category_id=laptops.id, seller_id=seller1.id),
            Product(name="HP Omen 15", description="Игровой ноутбук с RTX 3070", price=150000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Lenovo Legion 5 Pro", description="Игровой ноутбук с QHD экраном", price=140000.0, stock=4, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Microsoft Surface Book 3", description="Ноутбук-трансформер", price=160000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="ASUS ROG Zephyrus G14", description="Компактный игровой ноутбук", price=130000.0, stock=4, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Dell Latitude 7420", description="Бизнес-ноутбук с защитой", price=95000.0, stock=6, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="HP Elite Dragonfly", description="Премиум ультрабук", price=145000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Acer Swift 3", description="Легкий ультрабук", price=65000.0, stock=8, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="Lenovo Yoga C940", description="Ноутбук-трансформер с 4K экраном", price=110000.0, stock=4, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="Dell Inspiron 15", description="Универсальный ноутбук для дома", price=58000.0, stock=9, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="HP Spectre x360", description="Премиум ноутбук-трансформер", price=125000.0, stock=5, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="Acer ConceptD 7", description="Ноутбук для креативных профессионалов", price=190000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Razer Book 13", description="Ультрабук для геймеров", price=135000.0, stock=4, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="ASUS ExpertBook B9", description="Самый легкий бизнес-ноутбук", price=150000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Lenovo ThinkPad P1", description="Мобильная рабочая станция", price=180000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Microsoft Surface Laptop Go", description="Компактный бюджетный ноутбук", price=65000.0, stock=7, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="HP ZBook Fury 15", description="Мобильная рабочая станция", price=200000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Dell Precision 5550", description="Рабочая станция в корпусе XPS", price=170000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Lenovo IdeaPad Flex 5", description="Ноутбук-трансформер с сенсорным экраном", price=75000.0, stock=6, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="Apple MacBook Pro 16", description="Профессиональный ноутбук для творчества", price=220000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="MSI Creator 17", description="Ноутбук с mini-LED экраном", price=210000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="ASUS Chromebook Flip", description="Компактный хромбук-трансформер", price=45000.0, stock=9, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="HP ProBook 450", description="Надежный бизнес-ноутбук", price=85000.0, stock=7, active=True, category_id=laptops.id, seller_id=seller5.id),
            Product(name="Dell G5 15", description="Бюджетный игровой ноутбук", price=90000.0, stock=5, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="Lenovo ThinkPad X13", description="Компактный бизнес-ноутбук", price=95000.0, stock=6, active=True, category_id=laptops.id, seller_id=seller5.id),
            Product(name="ASUS VivoBook S15", description="Стильный ноутбук с подсветкой клавиатуры", price=68000.0, stock=8, active=True, category_id=laptops.id, seller_id=seller1.id),
            Product(name="HP Envy 13", description="Премиум ультрабук с алюминиевым корпусом", price=92000.0, stock=6, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="Acer Aspire 5", description="Бюджетный ноутбук с хорошей производительностью", price=55000.0, stock=10, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="Lenovo Legion 7", description="Топовый игровой ноутбук", price=160000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="ASUS ROG Flow X13", description="Компактный игровой ноутбук-трансформер", price=140000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="HP ZBook Studio", description="Мощная рабочая станция", price=180000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Microsoft Surface Pro 8", description="Планшет-трансформер с клавиатурой", price=120000.0, stock=5, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="Lenovo ThinkBook 15", description="Бизнес-ноутбук с современным дизайном", price=78000.0, stock=7, active=True, category_id=laptops.id, seller_id=seller5.id),
            Product(name="Dell Alienware m15 R5", description="Игровой ноутбук с механической клавиатурой", price=170000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="HP Omen X 2S", description="Игровой ноутбук с вторым экраном", price=190000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="ASUS ZenBook Duo", description="Ноутбук с двумя экранами", price=160000.0, stock=4, active=True, category_id=laptops.id, seller_id=seller1.id),
            Product(name="MSI GE76 Raider", description="Мощный игровой ноутбук", price=200000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller4.id),
            Product(name="Lenovo Yoga 9i", description="Премиум ноутбук-трансформер", price=130000.0, stock=5, active=True, category_id=laptops.id, seller_id=seller6.id),
            Product(name="Acer Spin 5", description="Ноутбук-трансформер с стилусом", price=90000.0, stock=7, active=True, category_id=laptops.id, seller_id=seller7.id),
            Product(name="Lenovo ThinkPad P15", description="Мощная мобильная рабочая станция", price=220000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="Dell Precision 7560", description="Рабочая станция для сложных задач", price=250000.0, stock=2, active=True, category_id=laptops.id, seller_id=seller8.id),
            Product(name="HP ZBook Create", description="Ноутбук для творческих профессионалов", price=190000.0, stock=3, active=True, category_id=laptops.id, seller_id=seller8.id),

            # Мониторы (50 товаров)
            Product(name="Dell UltraSharp 24", description="Монитор 24 дюйма с IPS матрицей", price=15500.0, stock=5, active=True, category_id=monitors.id, seller_id=seller2.id),
            Product(name="Samsung Odyssey G7", description="Игровой монитор 27'' 240Hz", price=42000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="LG 27GL850", description="Монитор 27'' Nano IPS", price=38000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="Xiaomi Mi 34", description="Ультраширокий монитор 34''", price=52000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller3.id),
            Product(name="BenQ PD2700U", description="Монитор 27'' 4K для дизайнеров", price=67000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="ASUS TUF Gaming VG27AQ", description="Игровой монитор 27'' 165Hz", price=45000.0, stock=6, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Philips 276E8VJSB", description="Монитор 27'' 4K UHD", price=29000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="AOC 24G2U", description="Игровой монитор 24'' 144Hz", price=32000.0, stock=8, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="ViewSonic XG2405", description="Игровой монитор 24'' 144Hz", price=28000.0, stock=7, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="ASUS ProArt PA278QV", description="Монитор для цветокоррекции", price=58000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="MSI Optix MAG274QRF", description="Игровой монитор 27'' 165Hz", price=47000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Dell Alienware AW2521HF", description="Игровой монитор 25'' 360Hz", price=65000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Gigabyte M27Q", description="Монитор 27'' 170Hz с QHD", price=52000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Samsung CRG5", description="Игровой монитор 27'' 240Hz", price=38000.0, stock=6, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Acer Predator XB273U", description="Игровой монитор 27'' 240Hz", price=72000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="LG UltraFine 4K", description="Монитор для Mac", price=45000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller6.id),
            Product(name="EIZO ColorEdge CG319X", description="Профессиональный монитор 4K", price=320000.0, stock=1, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="ASUS TUF Gaming VG279QM", description="Игровой монитор 27'' 280Hz", price=49000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="BenQ EX2780Q", description="Монитор с HDR и встроенными колонками", price=54000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="Samsung Space Monitor", description="Монитор с эргономичной подставкой", price=35000.0, stock=7, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="ViewSonic VP2768", description="Профессиональный монитор для дизайна", price=62000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="ASUS ROG Swift PG259QN", description="Игровой монитор 360Hz", price=85000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="LG 27UK850", description="Монитор 4K с USB-C", price=67000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="MSI PS321URV", description="Монитор 4K HDR 600", price=88000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Dell S2721DGF", description="Игровой монитор 27'' 165Hz", price=55000.0, stock=6, active=True, category_id=monitors.id, seller_id=seller2.id),
            Product(name="Samsung Odyssey G9", description="Суперширокий игровой монитор 49''", price=150000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="LG 38WN95C", description="Ультраширокий монитор 38''", price=120000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="ASUS PA32UCX", description="Профессиональный монитор 4K HDR", price=250000.0, stock=1, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="EIZO FlexScan EV2780", description="Эргономичный офисный монитор", price=75000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller5.id),
            Product(name="ASUS ROG Strix XG27UQ", description="Игровой монитор 4K 144Hz", price=95000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="BenQ EW3280U", description="Монитор 32'' 4K с HDR", price=78000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="Acer Predator X35", description="Игровой монитор с изогнутым экраном", price=180000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="ViewSonic Elite XG270QG", description="Игровой монитор с G-Sync", price=65000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Samsung UR59C", description="Ультраширокий монитор 32''", price=48000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="LG 27UL850", description="Монитор 4K с HDR10", price=62000.0, stock=6, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="ASUS ProArt PA34VC", description="Профессиональный изогнутый монитор", price=110000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="AOC CU34G2X", description="Игровой ультраширокий монитор", price=65000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="MSI Optix MAG322CQR", description="Игровой монитор 32'' с изогнутым экраном", price=58000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="LG 34WN80C", description="Ультраширокий монитор для работы", price=75000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="Samsung CJ79", description="Ультраширокий монитор с Thunderbolt", price=95000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="Dell UltraSharp 32", description="Монитор 4K для профессионалов", price=85000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="BenQ PD3200U", description="Монитор для дизайнеров 32'' 4K", price=90000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="LG 27GN950", description="Игровой монитор 4K 144Hz", price=110000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="ASUS TUF Gaming VG32VQ", description="Игровой монитор с изогнутым экраном", price=52000.0, stock=6, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Acer Predator XB323U", description="Игровой монитор 32'' 170Hz", price=95000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="Samsung ViewFinity S8", description="Профессиональный монитор 4K", price=100000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="LG UltraFine 5K", description="Монитор для творческих профессионалов", price=150000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller6.id),
            Product(name="BenQ EX3501R", description="Ультраширокий изогнутый монитор", price=85000.0, stock=4, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="Dell S3220DGF", description="Игровой монитор 32'' с изогнутым экраном", price=70000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller2.id),
            Product(name="ASUS ROG Swift PG32UQX", description="Игровой монитор 4K 144Hz с Mini-LED", price=300000.0, stock=1, active=True, category_id=monitors.id, seller_id=seller4.id),
            Product(name="LG 48CX", description="OLED монитор/телевизор 48''", price=140000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller1.id),
            Product(name="Samsung S80A", description="Монитор для бизнеса 27'' 4K", price=65000.0, stock=5, active=True, category_id=monitors.id, seller_id=seller5.id),
            Product(name="ASUS PA34VC", description="Профессиональный ультраширокий монитор", price=120000.0, stock=3, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="BenQ SW321C", description="Фото-монитор 32'' 4K", price=180000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller8.id),
            Product(name="LG 38GL950G", description="Ультраширокий игровой монитор", price=160000.0, stock=2, active=True, category_id=monitors.id, seller_id=seller4.id),

            # Мыши (30 товаров)
            Product(name="Logitech MX Master 3", description="Беспроводная мышь для профессионалов", price=2700.0, stock=25, active=True, category_id=mice.id, seller_id=seller1.id),
            Product(name="Razer DeathAdder V2", description="Игровая мышь с оптическим сенсором", price=4500.0, stock=15, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="SteelSeries Rival 3", description="Игровая мышь с RGB подсветкой", price=3200.0, stock=20, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Apple Magic Mouse 2", description="Беспроводная мышь для Mac", price=6900.0, stock=7, active=True, category_id=mice.id, seller_id=seller6.id),
            Product(name="HyperX Pulsefire Haste", description="Легкая игровая мышь", price=3800.0, stock=18, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Corsair Dark Core RGB", description="Беспроводная игровая мышь", price=5200.0, stock=10, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Zowie EC2", description="Игровая мышь для киберспорта", price=5500.0, stock=12, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Logitech G Pro X Superlight", description="Профессиональная беспроводная мышь", price=8900.0, stock=9, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Razer Viper Ultimate", description="Беспроводная игровая мышь", price=9500.0, stock=8, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="SteelSeries Aerox 3", description="Легкая беспроводная мышь", price=6500.0, stock=10, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Logitech G502 Hero", description="Игровая мышь с настраиваемым весом", price=5800.0, stock=14, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="ASUS ROG Chakram", description="Игровая мышь с джойстиком", price=12000.0, stock=5, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Razer Naga Pro", description="Мышь с заменяемыми боковыми панелями", price=13000.0, stock=6, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Corsair M65 RGB Elite", description="Игровая мышь с алюминиевым корпусом", price=7500.0, stock=9, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Glorious Model O", description="Ультралегкая игровая мышь", price=5000.0, stock=12, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Microsoft Surface Mouse", description="Элегантная беспроводная мышь", price=4500.0, stock=15, active=True, category_id=mice.id, seller_id=seller6.id),
            Product(name="Logitech MX Anywhere 3", description="Компактная беспроводная мышь", price=6500.0, stock=11, active=True, category_id=mice.id, seller_id=seller1.id),
            Product(name="Razer Basilisk V3", description="Игровая мышь с быстрой прокруткой", price=8500.0, stock=7, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="SteelSeries Rival 600", description="Игровая мышь с двойным сенсором", price=7800.0, stock=8, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="ASUS TUF M3", description="Прочная игровая мышь", price=3500.0, stock=20, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="HyperX Pulsefire Dart", description="Беспроводная игровая мышь", price=7000.0, stock=9, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Logitech G903", description="Беспроводная игровая мышь", price=11000.0, stock=6, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Razer Orochi V2", description="Компактная беспроводная мышь", price=6000.0, stock=10, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Corsair Ironclaw RGB", description="Игровая мышь для больших рук", price=6800.0, stock=8, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Glorious Model D", description="Эргономичная игровая мышь", price=5500.0, stock=11, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="Logitech MX Vertical", description="Эргономичная вертикальная мышь", price=8500.0, stock=7, active=True, category_id=mice.id, seller_id=seller1.id),
            Product(name="Razer Basilisk X Hyperspeed", description="Беспроводная игровая мышь", price=5000.0, stock=12, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="SteelSeries Prime", description="Игровая мышь с магнитными кнопками", price=9000.0, stock=6, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="ASUS ROG Gladius II", description="Игровая мышь с заменяемыми переключателями", price=7500.0, stock=8, active=True, category_id=mice.id, seller_id=seller4.id),
            Product(name="HyperX Pulsefire Surge", description="Игровая мышь с RGB подсветкой", price=5500.0, stock=10, active=True, category_id=mice.id, seller_id=seller4.id),

            # Клавиатуры (30 товаров)
            Product(name="Logitech G Pro X", description="Механическая игровая клавиатура с заменяемыми переключателями", price=12000.0, stock=15, active=True, category_id=keyboards.id, seller_id=seller1.id),
            Product(name="Razer BlackWidow V3", description="Механическая клавиатура с переключателями Razer Green", price=11000.0, stock=12, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="SteelSeries Apex Pro", description="Механическая клавиатура с регулируемым ходом клавиш", price=15000.0, stock=8, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Corsair K95 RGB Platinum", description="Механическая клавиатура с алюминиевой рамкой", price=18000.0, stock=6, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="HyperX Alloy Origins", description="Компактная механическая клавиатура", price=9000.0, stock=18, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="ASUS ROG Strix Scope", description="Игровая механическая клавиатура с RGB", price=13000.0, stock=10, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Ducky One 3", description="Механическая клавиатура с PBT клавишами", price=9500.0, stock=9, active=True, category_id=keyboards.id, seller_id=seller5.id),
            Product(name="Keychron K8", description="Беспроводная механическая клавиатура", price=8500.0, stock=14, active=True, category_id=keyboards.id, seller_id=seller5.id),
            Product(name="Logitech MX Keys", description="Беспроводная клавиатура для профессионалов", price=10000.0, stock=20, active=True, category_id=keyboards.id, seller_id=seller1.id),
            Product(name="Razer Huntsman Mini", description="60% механическая клавиатура с оптическими переключателями", price=11000.0, stock=11, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="SteelSeries Apex 3", description="Мембранная игровая клавиатура с RGB", price=6000.0, stock=25, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Corsair K70 RGB MK.2", description="Механическая клавиатура с Cherry MX Red", price=14000.0, stock=7, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="HyperX Alloy FPS Pro", description="Компактная механическая клавиатура для FPS", price=7500.0, stock=16, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="ASUS ROG Claymore II", description="Модульная механическая клавиатура", price=17000.0, stock=5, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Apple Magic Keyboard", description="Беспроводная клавиатура для Mac", price=12000.0, stock=12, active=True, category_id=keyboards.id, seller_id=seller6.id),
            Product(name="Logitech K380", description="Компактная беспроводная клавиатура", price=3500.0, stock=30, active=True, category_id=keyboards.id, seller_id=seller1.id),
            Product(name="Razer Ornata V2", description="Гибридная мембранно-механическая клавиатура", price=8000.0, stock=13, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="SteelSeries Apex 7", description="Механическая клавиатура с OLED дисплеем", price=12500.0, stock=9, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Corsair Strafe RGB MK.2", description="Механическая клавиатура с Cherry MX Silent", price=13000.0, stock=8, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="HyperX Alloy Elite 2", description="Механическая клавиатура с медиа-панелью", price=11000.0, stock=10, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="ASUS TUF Gaming K3", description="Мембранная игровая клавиатура", price=5000.0, stock=22, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Microsoft Surface Keyboard", description="Беспроводная клавиатура с элегантным дизайном", price=8500.0, stock=15, active=True, category_id=keyboards.id, seller_id=seller6.id),
            Product(name="Logitech G915 TKL", description="Беспроводная низкопрофильная механическая клавиатура", price=20000.0, stock=6, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Razer Cynosa V2", description="Мембранная RGB клавиатура", price=5500.0, stock=18, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="SteelSeries Apex 5", description="Гибридная механическая клавиатура", price=9500.0, stock=12, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Corsair K63 Wireless", description="Беспроводная механическая клавиатура", price=11000.0, stock=9, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="HyperX Alloy Core RGB", description="Мембранная RGB клавиатура", price=4500.0, stock=25, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="ASUS ROG Falchion", description="Компактная беспроводная механическая клавиатура", price=14000.0, stock=7, active=True, category_id=keyboards.id, seller_id=seller4.id),
            Product(name="Varmilo VA87M", description="Механическая клавиатура с дизайнерскими клавишами", price=13000.0, stock=5, active=True, category_id=keyboards.id, seller_id=seller5.id),
            Product(name="Ducky Shine 7", description="Механическая клавиатура с металлическим корпусом", price=15000.0, stock=6, active=True, category_id=keyboards.id, seller_id=seller5.id),

            #Наушники (20 товаров)
            Product(name="Sony WH-1000XM4", description="Беспроводные наушники с шумоподавлением", price=25000.0, stock=10, active=True, category_id=headphones.id, seller_id=seller2.id),
            Product(name="Bose QuietComfort 45", description="Наушники с активным шумоподавлением", price=23000.0, stock=8, active=True, category_id=headphones.id, seller_id=seller2.id),
            Product(name="Sennheiser HD 660 S", description="Открытые наушники для аудиофилов", price=35000.0, stock=5, active=True, category_id=headphones.id, seller_id=seller3.id),
            Product(name="Apple AirPods Max", description="Беспроводные наушники премиум-класса", price=60000.0, stock=6, active=True, category_id=headphones.id, seller_id=seller6.id),
            Product(name="Audio-Technica ATH-M50x", description="Студийные мониторные наушники", price=15000.0, stock=15, active=True, category_id=headphones.id, seller_id=seller3.id),
            Product(name="SteelSeries Arctis Pro", description="Игровые наушники с Hi-Res звуком", price=18000.0, stock=12, active=True, category_id=headphones.id, seller_id=seller4.id),
            Product(name="Razer BlackShark V2", description="Игровые наушники с микрофоном", price=9000.0, stock=20, active=True, category_id=headphones.id, seller_id=seller4.id),
            Product(name="HyperX Cloud II", description="Игровые наушники с виртуальным 7.1", price=8000.0, stock=25, active=True, category_id=headphones.id, seller_id=seller4.id),
            Product(name="Beyerdynamic DT 990 Pro", description="Студийные наушники с открытой конструкцией", price=17000.0, stock=9, active=True, category_id=headphones.id, seller_id=seller3.id),
            Product(name="JBL Quantum 800", description="Беспроводные игровые наушники", price=14000.0, stock=11, active=True, category_id=headphones.id, seller_id=seller4.id),
            Product(name="Logitech G Pro X", description="Игровые наушники с Blue Voice", price=12000.0, stock=14, active=True, category_id=headphones.id, seller_id=seller4.id),
            Product(name="Sony MDR-7506", description="Профессиональные наушники для студии", price=10000.0, stock=18, active=True, category_id=headphones.id, seller_id=seller2.id),
            Product(name="Bose SoundLink Around-Ear", description="Беспроводные наушники с качественным звуком", price=16000.0, stock=10, active=True, category_id=headphones.id, seller_id=seller2.id),
            Product(name="Sennheiser Momentum 3", description="Беспроводные наушники премиум-класса", price=28000.0, stock=7, active=True, category_id=headphones.id, seller_id=seller3.id),
            Product(name="Apple AirPods Pro", description="Беспроводные наушники с шумоподавлением", price=22000.0, stock=20, active=True, category_id=headphones.id, seller_id=seller6.id),
            Product(name="Jabra Elite 85h", description="Наушники с умным шумоподавлением", price=18000.0, stock=12, active=True, category_id=headphones.id, seller_id=seller2.id),
            Product(name="AKG K371", description="Закрытые студийные наушники", price=13000.0, stock=14, active=True, category_id=headphones.id, seller_id=seller3.id),
            Product(name="Corsair Virtuoso RGB", description="Беспроводные игровые наушники", price=16000.0, stock=9, active=True, category_id=headphones.id, seller_id=seller4.id),
            Product(name="Philips Fidelio X2HR", description="Открытые наушники Hi-Fi класса", price=14000.0, stock=8, active=True, category_id=headphones.id, seller_id=seller3.id),
            Product(name="Marshall Major IV", description="Беспроводные наушники с длительным зарядом", price=11000.0, stock=15, active=True, category_id=headphones.id, seller_id=seller2.id),

            #Комплектующие (20 товаров)

            Product(name="Intel Core i9-12900K", description="Процессор 16-ядерный 24-потока", price=45000.0, stock=8, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="AMD Ryzen 9 5950X", description="16-ядерный процессор AM4", price=50000.0, stock=6, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="NVIDIA GeForce RTX 3090", description="Видеокарта 24GB GDDR6X", price=150000.0, stock=3, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="AMD Radeon RX 6900 XT", description="Видеокарта 16GB GDDR6", price=120000.0, stock=4, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Samsung 980 Pro 1TB", description="NVMe SSD PCIe 4.0", price=15000.0, stock=15, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Crucial Ballistix 32GB", description="DDR4 3600MHz RAM", price=12000.0, stock=20, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="ASUS ROG Maximus Z690", description="Материнская плата для Intel", price=35000.0, stock=7, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="MSI MPG B550 Gaming", description="Материнская плата для AMD", price=15000.0, stock=12, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Corsair RM850x", description="Блок питания 850W 80+ Gold", price=13000.0, stock=10, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Noctua NH-D15", description="Кулер для процессора", price=9000.0, stock=15, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="NZXT Kraken X73", description="СЖО 360mm RGB", price=14000.0, stock=8, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Fractal Design Meshify C", description="Корпус с хорошей вентиляцией", price=8000.0, stock=18, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Seagate IronWolf 4TB", description="Жесткий диск для NAS", price=10000.0, stock=12, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="WD Black SN850 1TB", description="NVMe SSD с теплорассеивателем", price=16000.0, stock=9, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="G.Skill Trident Z RGB", description="32GB DDR4 3200MHz", price=14000.0, stock=11, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="ASUS TUF Gaming GT501", description="Игровой корпус с RGB", price=12000.0, stock=10, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="EVGA SuperNOVA 1000W", description="Блок питания 80+ Platinum", price=20000.0, stock=6, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Deepcool AS500 Plus", description="Башенный кулер с двумя вентиляторами", price=6000.0, stock=20, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Lian Li PC-O11 Dynamic", description="Корпус для моддинга", price=15000.0, stock=7, active=True, category_id=components.id, seller_id=seller7.id),
            Product(name="Thermaltake ToughRam", description="RGB память DDR4 16GB", price=9000.0, stock=15, active=True, category_id=components.id, seller_id=seller7.id)

        ]
        session.add_all(products)
        await session.commit()
        print("БД успешно заполнена начальными товарами.")
