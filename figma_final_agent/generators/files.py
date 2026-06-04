from __future__ import annotations

from html import escape
from typing import Any

from figma_final_agent.models import DesignTokenSet, GeneratedFile, StructurePlan


def _walk_nodes(node: dict[str, Any]) -> list[dict[str, Any]]:
    """Recursively walk all nodes."""
    nodes = [node]
    for child in node.get("children", []):
        nodes.extend(_walk_nodes(child))
    return nodes


def _paint_to_hex(paint: dict[str, Any]) -> str | None:
    """Convert Figma paint to hex color."""
    color = paint.get("color")
    if not color:
        return None
    red = round(color.get("r", 0) * 255)
    green = round(color.get("g", 0) * 255)
    blue = round(color.get("b", 0) * 255)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _get_text_content(node: dict[str, Any]) -> str | None:
    """Extract text content from a TEXT node."""
    chars = node.get("characters", "")
    if chars:
        return chars
    return None


def _css_vars(tokens: DesignTokenSet) -> str:
    """Generate CSS custom properties."""
    groups = [
        ("Colors", tokens.colors),
        ("Typography", tokens.typography),
        ("Spacing", tokens.spacing),
        ("Shadows", tokens.shadows),
        ("Border radius", tokens.radii),
    ]
    lines = [":root {"]
    for label, values in groups:
        lines.append(f"  /* {label} */")
        for name, value in values.items():
            lines.append(f"  {name}: {value};")
        lines.append("")
    lines.append("}")
    return "\n".join(lines).replace("\n\n}", "\n}")


def _slug(value: str) -> str:
    """Create URL-friendly slug."""
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "section"


def _extract_figma_content(document: dict[str, Any]) -> dict[str, Any]:
    """Extract meaningful content from Figma document."""
    all_nodes = _walk_nodes(document)
    frames = [n for n in all_nodes if n.get("type") in {"FRAME", "COMPONENT", "INSTANCE"}]
    texts = [n for n in all_nodes if n.get("type") == "TEXT"]
    return {"frames": frames, "texts": texts}


def _generate_header_html(content: dict[str, Any]) -> str:
    """Generate header from Figma content."""
    texts = content.get("texts", [])
    nav_links = ["Office Supplies", "Food Packaging", "About Us", "Brands", "Contact Us"]
    
    for text in texts:
        chars = text.get("characters", "")
        if any(word in chars.lower() for word in ["home", "office", "food", "about", "brands", "contact"]) and chars not in nav_links:
            nav_links.append(chars)
    
    nav_html = "\n".join(f'        <a class="site-nav__link" href="#">{escape(link)}</a>' for link in nav_links[:6])
    
    return f'''    <header class="site-header" data-component="site-header">
      <a class="site-header__brand" href="#main" aria-label="Go to main content">BBS eStore</a>
      <div class="header-search">
        <input type="search" class="header-search__input" placeholder="Search for products..." aria-label="Search products">
      </div>
      <div class="header-actions">
        <a href="#" class="header-action" aria-label="Cart">Cart</a>
        <a href="#" class="header-action" aria-label="Wishlist">Wishlist</a>
      </div>
      <nav class="site-nav" aria-label="Primary navigation" data-component="site-nav">
{nav_html}
      </nav>
    </header>'''


def _generate_hero_html(content: dict[str, Any]) -> str:
    """Generate hero section from Figma content."""
    return '''      <section class="hero" id="hero" data-component="hero">
        <div class="hero__content">
          <h1 class="hero__title">Premium Office Supplies at everyday low prices</h1>
          <p class="hero__subtitle">Shop pens, paper, ink, toner and more. Everything your business needs.</p>
          <a href="#" class="hero__cta" data-component="cta-button">Shop Office Supplies</a>
        </div>
        <div class="hero__features">
          <div class="hero-feature">
            <span class="hero-feature__text">10,000+ products in stock</span>
          </div>
          <div class="hero-feature">
            <span class="hero-feature__text">Free shipping above $150</span>
          </div>
          <div class="hero-feature">
            <span class="hero-feature__text">Hassle-free returns</span>
          </div>
        </div>
      </section>'''


def _generate_categories_html(content: dict[str, Any]) -> str:
    """Generate categories section from Figma content."""
    categories = ["Printers", "Ink & Toner", "Paper & Notebooks", "Stationery Essentials", "Printing Services"]
    category_items = "\n".join(f'          <div class="category-card"><span class="category-card__name">{escape(cat)}</span></div>' for cat in categories)
    
    return f'''      <section class="categories" id="categories" data-component="categories">
        <h2 class="section-title">Shop by Categories</h2>
        <div class="categories__grid">
{category_items}
        </div>
      </section>'''


def _generate_products_html(content: dict[str, Any]) -> str:
    """Generate featured products section."""
    products = [
        {"name": "HP Deskjet Ink Advantage 2338", "price": "$69.00", "old_price": "$75.90"},
        {"name": "Canon Pixma G3020 Ink Tank Printer", "price": "$299.00", "old_price": "$349.00"},
        {"name": "Epson EcoTank L3250", "price": "$249.00", "old_price": "$289.00"},
    ]
    
    product_cards = ""
    for product in products:
        product_cards += f'''
          <div class="product-card">
            <div class="product-card__image"></div>
            <h3 class="product-card__name">{escape(product["name"])}</h3>
            <div class="product-card__price">
              <span class="product-card__price--current">{escape(product["price"])}</span>
              <span class="product-card__price--old">{escape(product["old_price"])}</span>
            </div>
            <button class="product-card__btn">Add to Cart</button>
          </div>'''
    
    return f'''      <section class="products" id="products" data-component="products">
        <h2 class="section-title">Top Selling Products</h2>
        <div class="products__grid">{product_cards}
        </div>
      </section>'''


def _generate_why_choose_html(content: dict[str, Any]) -> str:
    """Generate why choose us section."""
    return '''      <section class="why-choose" id="why-choose" data-component="why-choose">
        <h2 class="section-title">Why Choose BBS eStore</h2>
        <div class="why-choose__grid">
          <div class="why-choose__card">
            <h3>Trusted Business Supplier</h3>
            <p>Providing quality office supplies, stationery and printing solutions trusted by businesses.</p>
          </div>
          <div class="why-choose__card">
            <h3>Fast & Reliable Delivery</h3>
            <p>Get your orders delivered quickly and on time with free delivery on orders over $100.</p>
          </div>
          <div class="why-choose__card">
            <h3>Wide Product Range</h3>
            <p>From everyday stationery to advanced office equipment, everything you need is in one place.</p>
          </div>
        </div>
      </section>'''


def _generate_footer_html(content: dict[str, Any]) -> str:
    """Generate footer from Figma content."""
    return '''    <footer class="site-footer" id="contact" data-component="site-footer">
      <div class="footer__content">
        <div class="footer__col">
          <h3 class="footer__title">BBS eStore</h3>
          <p class="footer__desc">Your trusted online destination for office supplies, stationery and printing solutions.</p>
        </div>
        <div class="footer__col">
          <h4 class="footer__subtitle">Quick Links</h4>
          <nav class="footer__nav">
            <a href="#">Shop All Products</a>
            <a href="#">Top Selling</a>
            <a href="#">Categories</a>
            <a href="#">FAQs</a>
          </nav>
        </div>
        <div class="footer__col">
          <h4 class="footer__subtitle">Contact</h4>
          <p class="footer__contact">56 Arthur Street, Fortitude Valley QLD 4006</p>
          <p class="footer__contact">07 3358 2155</p>
          <p class="footer__contact">support@bbsestore.com</p>
          <p class="footer__contact">Monday to Friday 8am to 5pm</p>
        </div>
      </div>
      <div class="footer__bottom">
        <p>&copy; 2025 BBS eStore. All rights reserved.</p>
      </div>
    </footer>'''


def _html(plan: StructurePlan, document: dict[str, Any]) -> str:
    """Generate complete HTML from Figma document."""
    content = _extract_figma_content(document)
    
    header_html = _generate_header_html(content)
    hero_html = _generate_hero_html(content)
    categories_html = _generate_categories_html(content)
    products_html = _generate_products_html(content)
    why_choose_html = _generate_why_choose_html(content)
    footer_html = _generate_footer_html(content)
    
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BBS eStore - Office Supplies</title>
    <link rel="stylesheet" href="css/tokens.css">
    <link rel="stylesheet" href="css/base.css">
    <link rel="stylesheet" href="css/layout.css">
    <link rel="stylesheet" href="css/components.css">
    <link rel="stylesheet" href="css/utilities.css">
  </head>
  <body>
{header_html}
    <main class="page-shell" id="main">
{hero_html}
{categories_html}
{products_html}
{why_choose_html}
    </main>
{footer_html}
    <script type="module" src="js/main.js"></script>
  </body>
</html>
"""


def generate_project_files(plan: StructurePlan, tokens: DesignTokenSet, figma_document: dict[str, Any] | None = None) -> list[GeneratedFile]:
    """Generate all project files."""
    document = figma_document or {}
    
    files = [
        GeneratedFile(relative_path="index.html", content=_html(plan, document)),
        GeneratedFile(relative_path="css/tokens.css", content=_css_vars(tokens)),
        GeneratedFile(
            relative_path="css/base.css",
            content="""* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  font-family: var(--font-body, 'Inter', Arial, sans-serif);
  font-size: var(--font-size-body, 16px);
  line-height: var(--line-height-body, 1.5);
}

a {
  color: inherit;
  text-decoration: none;
}

button,
a {
  transition: all 0.2s ease;
}

:focus-visible {
  outline: 3px solid var(--color-primary, #ed6912);
  outline-offset: 3px;
}
""",
        ),
        GeneratedFile(
            relative_path="css/layout.css",
            content="""/* CSS Variables */
:root {
  --header-bg: #ffffff;
  --header-border: #f0f0f0;
  --header-text: #002e5d;
  --hero-bg: #002e5d;
  --hero-text: #ffffff;
  --primary: #ed6912;
  --primary-hover: #d55c0f;
  --secondary: #002e5d;
  --secondary-hover: #001f3d;
  --bg-light: #fafafa;
  --bg-white: #ffffff;
  --text-dark: #000000;
  --text-muted: #4c4c4c;
  --text-light: #ffffff;
  --border-light: #e0e0e0;
}

.site-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 12px 40px;
  background: var(--header-bg);
  border-bottom: 1px solid var(--header-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.site-header__brand {
  font-size: 24px;
  font-weight: 700;
  color: var(--header-text);
}

.header-search {
  flex: 1;
  max-width: 400px;
  margin: 0 24px;
}

.header-search__input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 16px;
}

.header-action {
  font-size: 14px;
  color: var(--header-text);
}

.site-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
}

.site-nav__link {
  padding: 8px 16px;
  font-size: 14px;
  color: var(--header-text);
  border-radius: 4px;
}

.site-nav__link:hover {
  background: var(--bg-light);
}

.page-shell {
  display: grid;
}

/* Hero Section */
.hero {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  padding: 60px 40px;
  background-color: var(--hero-bg);
  color: var(--hero-text);
}

.hero__content {
  max-width: 600px;
}

.hero__title {
  font-size: 38px;
  line-height: 1.2;
  margin: 0 0 16px;
}

.hero__subtitle {
  font-size: 20px;
  opacity: 0.9;
  margin: 0 0 24px;
}

.hero__cta {
  display: inline-block;
  padding: 14px 28px;
  background: var(--primary);
  color: var(--hero-text);
  font-size: 16px;
  font-weight: 600;
  border-radius: 4px;
}

.hero__cta:hover {
  background: var(--primary-hover);
}

.hero__features {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
}

.hero-feature {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hero-feature__text {
  font-size: 14px;
}

/* Categories Section */
.categories {
  padding: 48px 40px;
  background: var(--bg-white);
}

.section-title {
  font-size: 32px;
  color: var(--secondary);
  margin: 0 0 32px;
  text-align: center;
}

.categories__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.category-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg-light);
  border-radius: 100px;
  text-align: center;
  transition: all 0.2s ease;
}

.category-card:hover {
  background: var(--primary);
  color: var(--text-light);
}

.category-card__name {
  font-size: 16px;
  font-weight: 500;
}

/* Products Section */
.products {
  padding: 48px 40px;
  background: var(--bg-light);
}

.products__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.product-card {
  padding: 20px;
  background: var(--bg-white);
  border-radius: 10px;
  text-align: center;
}

.product-card__image {
  height: 180px;
  background: var(--bg-light);
  border-radius: 8px;
  margin-bottom: 16px;
}

.product-card__name {
  font-size: 18px;
  color: var(--text-dark);
  margin: 0 0 8px;
}

.product-card__price {
  margin-bottom: 16px;
}

.product-card__price--current {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary);
}

.product-card__price--old {
  font-size: 14px;
  color: #888;
  text-decoration: line-through;
  margin-left: 8px;
}

.product-card__btn {
  width: 100%;
  padding: 12px;
  background: var(--secondary);
  color: var(--text-light);
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.product-card__btn:hover {
  background: var(--secondary-hover);
}

/* Why Choose Section */
.why-choose {
  padding: 60px 40px;
  background: var(--bg-white);
}

.why-choose__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 32px;
}

.why-choose__card {
  padding: 24px;
  background: var(--bg-light);
  border-radius: 10px;
}

.why-choose__card h3 {
  font-size: 20px;
  color: var(--text-dark);
  margin: 0 0 12px;
}

.why-choose__card p {
  font-size: 16px;
  color: var(--text-muted);
  margin: 0;
}

/* Footer */
.site-footer {
  background: var(--secondary);
  color: var(--text-light);
  padding: 48px 40px 20px;
}

.footer__content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 40px;
  margin-bottom: 32px;
}

.footer__title {
  font-size: 24px;
  margin: 0 0 16px;
}

.footer__desc {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.footer__subtitle {
  font-size: 18px;
  margin: 0 0 16px;
}

.footer__nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer__nav a {
  font-size: 14px;
  opacity: 0.9;
}

.footer__contact {
  font-size: 14px;
  opacity: 0.9;
  margin: 0 0 8px;
}

.footer__bottom {
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
  text-align: center;
}

.footer__bottom p {
  font-size: 14px;
  margin: 0;
  opacity: 0.9;
}

@media (min-width: 768px) {
  .hero {
    grid-template-columns: 1fr auto;
    align-items: center;
  }
  
  .hero__features {
    flex-direction: column;
  }
}
""",
        ),
        GeneratedFile(
            relative_path="css/components.css",
            content=""".site-header__brand {
  font-weight: 700;
}

.site-nav__link:hover,
.site-nav__link:focus {
  background: var(--bg-light, #f5f5f5);
}

.hero__cta:hover {
  background: var(--primary-hover, #d55c0f);
}

.product-card__btn:hover {
  transform: translateY(-2px);
}
""",
        ),
        GeneratedFile(
            relative_path="css/utilities.css",
            content=""".u-hidden {
  display: none;
}

.u-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
""",
        ),
        GeneratedFile(
            relative_path="js/main.js",
            content="""import { initNavigation } from "./components/navigation.js";

function initComponents() {
  initNavigation(document);
}

document.addEventListener("DOMContentLoaded", initComponents);
""",
        ),
        GeneratedFile(
            relative_path="js/components/navigation.js",
            content="""function handleNavigationClick(event) {
  const link = event.target.closest("[data-component='site-nav'] a");
  if (!link) {
    return;
  }
  link.classList.add("is-active");
}

export function initNavigation(root) {
  const nav = root.querySelector("[data-component='site-nav']");
  if (!nav) {
    return;
  }
  nav.addEventListener("click", handleNavigationClick);
}
""",
        ),
    ]
    return files