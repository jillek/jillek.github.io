import os
import re
from bs4 import BeautifulSoup, NavigableString
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
SOURCE_DIR = os.getcwd()
TARGET_DIR = os.path.join(SOURCE_DIR, "nl")
TARGET_LANG = 'nl'
BASE_URL = "https://www.jillekuipers.com"

FILES_TO_PROCESS = [
    'index.html', 'blog.html', 'ai-native.html', 'innovation-audit.html',
    'case-study-jccpa.html', 'case-study-hortipower.html', 
    'case-study-transformation.html', 'resume.html'
]

# Words to keep in English
PROTECTED_TERMS = [
    "S-Curve", "HealthTech", "AgTech", "IoT", "SaaS", "LaaS", "E-Ink", 
    "Innovation Audit", "Y-Combinator", "Luxbalance", "HortiPower", 
    "RoomYou", "Sharepal", "iFLEXTUBE", "Shopify", "BMW", "Spotify", 
    "Philips", "Nespresso", "Marriott", "Dole", "Hilton", "Wynn", 
    "Okura", "Schiphol", "PVMC", "Univé", "JCCPA"
]

# --- CORPORATE DUTCH OVERRIDES ---
MANUAL_TRANSLATIONS = {
    "Hey, I'm Jille, an Innovation & Technology Leader specializing in Human-Centric Innovation and Digital Transformation.":
    "Hallo, ik ben Jille. Als Innovation & Technology Leader ben ik gespecialiseerd in mensgerichte innovatie en digitale transformatie.",

    "I've led complex system and product innovations in Technology, Health care, Agriculture and Hospitality, and science-led startup from zero to $1.7M in annual sales. My work bridges the gap between massive portfolio management (€300M+) and talking to end-users across global markets to build products people need.":
    "Ik heb leiding gegeven aan complexe systeem- en productinnovaties in de technologie, gezondheidszorg, landbouw en hospitality. Daarnaast schaalde ik een wetenschappelijke startup van nul naar $1,7M jaaromzet. Mijn werk slaat een brug tussen grootschalig portfoliobeheer (€300M+) en directe interactie met eindgebruikers in wereldwijde markten, om producten te realiseren die er echt toe doen.",

    "My approach is data-centric and science-backed. I care about real outcomes, from optimizing growth for 10 million lab plants annually to leveraging IoT and AI to address urgent societal needs, such as improving the quality of life for those living with dementia and supporting ageing at home.":
    "Mijn aanpak is datagedreven en wetenschappelijk onderbouwd. Ik stuur op concrete resultaten: van het optimaliseren van de groei van 10 miljoen laboratoriumplanten per jaar tot het inzetten van IoT en AI voor urgente maatschappelijke vraagstukken, zoals de kwaliteit van leven bij dementie en langer thuis wonen.",

    "Outside of professional innovation, I love spending time with my little ones.":
    "Naast mijn passie voor innovatie geniet ik van de tijd met mijn gezin.",

    "Leveraging AI with a human-in-the-loop can help scale-up, improve customer experience and drive growth. e.g. I optimized IoT monitoring for the most precise care environments; from HealthTech patient support to AgTech plant health.":
    "De inzet van AI met een 'human-in-the-loop' benadering maakt schaalvergroting mogelijk, verbetert de klantervaring en stimuleert groei. Ik optimaliseerde bijvoorbeeld IoT-monitoring voor hoognauwkeurige zorgomgevingen; van patiëntondersteuning in HealthTech tot plantgezondheid in AgTech.",
    
    "I lead teams to make products people need, from complex problems to insights & science-based solutions to drive growth":
    "Ik leid teams in het ontwikkelen van producten die mensen nodig hebben: van complexe vraagstukken naar inzichten en wetenschappelijk onderbouwde oplossingen die groei stimuleren."
}

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

translator = GoogleTranslator(source='en', target=TARGET_LANG)

def fix_paths_for_dutch(soup):
    """
    Updates links, scripts and images to point UP one level (../) 
    """
    # 1. Fix Images
    for img in soup.find_all('img'):
        if img.get('src') and not img['src'].startswith(('http', '//', 'data:', '../')):
            img['src'] = f"../{img['src']}"
        if img.get('srcset'):
            new_srcset = []
            for src in img['srcset'].split(','):
                parts = src.strip().split(' ')
                url = parts[0]
                if not url.startswith(('http', '//', 'data:', '../')):
                    parts[0] = f"../{url}"
                new_srcset.append(' '.join(parts))
            img['srcset'] = ', '.join(new_srcset)

    # 2. Fix CSS, Favicons, and FONTS
    for link in soup.find_all('link'):
        # Skip hreflang tags
        if link.get('rel') == ['alternate']: continue
        
        if link.get('href') and not link['href'].startswith(('http', '//', 'data:', '../', '#', 'mailto:')):
            link['href'] = f"../{link['href']}"

    # 3. Fix Scripts (Tailwind etc)
    for script in soup.find_all('script'):
        if script.get('src') and not script['src'].startswith(('http', '//', 'data:', '../')):
            script['src'] = f"../{script['src']}"

def add_hreflang_to_soup(soup, filename):
    if not soup or not soup.head: return
    # Remove existing to prevent duplicates
    for link in soup.find_all("link", rel="alternate"):
        if link.get("hreflang"): link.decompose()

    en_url = f"{BASE_URL}/{filename}"
    nl_url = f"{BASE_URL}/nl/{filename}"
    
    tags = [
        soup.new_tag("link", rel="alternate", hreflang="en", href=en_url),
        soup.new_tag("link", rel="alternate", hreflang="nl", href=nl_url),
        soup.new_tag("link", rel="alternate", hreflang="x-default", href=en_url)
    ]
    for tag in tags: soup.head.append(tag)

def inject_toggle(soup, current_file, is_dutch=False):
    """Smartly injects the EN/NL toggle."""
    
    en_link = f"../{current_file}" if is_dutch else "#"
    nl_link = "#" if is_dutch else f"nl/{current_file}"
    
    active_cls = "text-[10px] font-black uppercase tracking-widest text-blue-600"
    inactive_cls = "text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-blue-600 transition-colors"

    # --- SAFE CLEANUP ---
    # Only remove the toggle if it matches the Specific Class structure
    # This prevents deleting the whole header
    for div in soup.find_all('div'):
        if div.has_attr('class'):
            classes = div['class']
            # We look for the unique combination of classes used in the toggle
            if 'border-l' in classes and 'space-x-2' in classes and 'ml-6' in classes:
                div.decompose()

    # --- CREATE TOGGLE ---
    toggle_html = f'''
    <div class="flex items-center ml-6 border-l border-slate-200 pl-6 space-x-2 pointer-events-auto">
        <a href="{en_link}" class="{active_cls if not is_dutch else inactive_cls}">EN</a>
        <span class="text-slate-300">/</span>
        <a href="{nl_link}" class="{active_cls if is_dutch else inactive_cls}">NL</a>
    </div>
    '''
    
    # Inject Desktop
    nav = soup.find('nav', class_=re.compile(r'hidden md:flex'))
    if nav:
        nav.append(BeautifulSoup(toggle_html, 'html.parser'))
    else:
        # Fallback
        header_row = soup.find('div', class_=re.compile(r'flex justify-between'))
        if header_row:
            children = header_row.find_all('div', recursive=False)
            if children:
                children[-1].append(BeautifulSoup(toggle_html, 'html.parser'))

    # Inject Mobile
    mobile_menu = soup.find('div', class_="md:hidden flex items-center")
    if mobile_menu:
        # Cleanup mobile specific
        for existing in mobile_menu.find_all('div', class_=re.compile("border-l")):
            existing.decompose()
        
        mobile_toggle = f'''
        <div class="flex items-center border-l border-slate-200 pl-4 ml-2 space-x-2">
            <a href="{en_link}" class="{active_cls if not is_dutch else inactive_cls}">EN</a>
            <span class="text-slate-300">/</span>
            <a href="{nl_link}" class="{active_cls if is_dutch else inactive_cls}">NL</a>
        </div>
        '''
        mobile_menu.append(BeautifulSoup(mobile_toggle, 'html.parser'))

def process_files():
    for filename in FILES_TO_PROCESS:
        file_path = os.path.join(SOURCE_DIR, filename)
        if not os.path.exists(file_path):
            print(f"Skipping {filename}")
            continue

        print(f"Processing: {filename}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_html = f.read()
            source_soup = BeautifulSoup(source_html, 'html.parser')

        # Update English
        add_hreflang_to_soup(source_soup, filename)
        inject_toggle(source_soup, filename, is_dutch=False)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(source_soup.prettify())

        # Create Dutch
        dutch_soup = BeautifulSoup(source_html, 'html.parser')
        dutch_soup.html['lang'] = TARGET_LANG
        
        fix_paths_for_dutch(dutch_soup)
        add_hreflang_to_soup(dutch_soup, filename)
        inject_toggle(dutch_soup, filename, is_dutch=True)

        if dutch_soup.title:
            try: dutch_soup.title.string = translator.translate(dutch_soup.title.string)
            except: pass

        tags_to_translate = ['p', 'h1', 'h2', 'h3', 'h4', 'span', 'li', 'a', 'td', 'div', 'strong', 'b', 'em']
        
        for tag in dutch_soup.find_all(tags_to_translate):
            if tag.find_parent(['script', 'style', 'svg']): continue
            if "EN" in tag.get_text() and "NL" in tag.get_text(): continue 
            
            clean_text = " ".join(tag.get_text().split())
            if clean_text in MANUAL_TRANSLATIONS:
                tag.string = MANUAL_TRANSLATIONS[clean_text]
                continue

            for content in tag.contents:
                if isinstance(content, NavigableString) and len(content.strip()) > 2:
                    text_val = content.strip()
                    if any(p in text_val for p in PROTECTED_TERMS) and len(text_val.split()) < 3: continue
                    try:
                        translated = translator.translate(text_val)
                        content.replace_with(translated)
                    except: continue

        output_path = os.path.join(TARGET_DIR, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dutch_soup.prettify())
        print(f" -> Generated nl/{filename}")

if __name__ == "__main__":
    process_files()
    print("\nSUCCESS: Headers fixed. Styles fixed.")