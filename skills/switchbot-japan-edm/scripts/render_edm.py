#!/usr/bin/env python3
"""Render a selected, evidence-backed recipe into editable email and review files.

This is a portable internal design adapter, not the frozen Ruby production runtime.
The optional WeasyPrint export typesets the same HTML without JavaScript/network;
it never reports browser or inbox-client QA as completed.
"""
from __future__ import annotations

import argparse
import base64
from datetime import date
import hashlib
import html
import io
import json
import mimetypes
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/history-recipes.json"
SUPPORTED = {
    "autumn-sale-open-v1": "featured_split_then_grid",
    "pd-sale-open-v1": "priority_split_then_grid",
    "category-security-v1": "scenario_pairs",
    "product-reveal-v1": "single_product_story",
    "autumn-catalog-v1": "dense_two_column_catalog",
}
TOKEN = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
OPTIONAL_MODULES = {"discovery", "coupon", "brand", "line"}


def h(value):
    return html.escape(str(value), quote=True)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def resource(path):
    p = Path(path)
    if not p.is_file() or not p.stat().st_size:
        raise ValueError(f"Missing local asset: {p.name}")
    mime = mimetypes.guess_type(p.name)[0]
    if mime not in {"image/png", "image/jpeg", "image/gif"}:
        raise ValueError("Product/email assets must be PNG, JPEG or GIF")
    return "data:" + mime + ";base64," + base64.b64encode(p.read_bytes()).decode()


def destination(value, fallback):
    if not value:
        return "{{" + fallback + "}}"
    if TOKEN.fullmatch(value):
        return value
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Email destinations must use HTTPS or unresolved tokens")
    return value


def sourced(value):
    """Evidence must name an actual source URL, never an unresolved destination token."""
    return isinstance(value, str) and not TOKEN.fullmatch(value) and destination(value, "SOURCE") == value


def offer_state(offer, channel):
    status = offer.get("status")
    if status not in {"CONFIRMED", "DRAFT"} or offer.get("sale_price_jpy") is None:
        return None
    if not offer.get("source"):
        return None
    if not sourced(offer["source"]):
        raise ValueError("Current price needs its actual source URL")
    if status == "DRAFT" and offer.get("channel") != channel:
        raise ValueError("Draft price needs its exact current channel")
    if offer.get("channel", channel) != channel:
        raise ValueError("Price channel differs from current email")
    price, old = offer["sale_price_jpy"], offer.get("reference_price_jpy")
    if not isinstance(price, int) or isinstance(price, bool) or price < 0:
        raise ValueError("Invalid current price")
    if old is not None and (not isinstance(old, int) or isinstance(old, bool) or old < price):
        raise ValueError("Invalid comparison price")
    return status


def validate_optional_modules(data):
    for name, enabled in data.get("module_enabled", {}).items():
        if name not in OPTIONAL_MODULES or not isinstance(enabled, bool):
            raise ValueError("Only optional discovery/coupon/brand/line modules may be toggled")
    for name in OPTIONAL_MODULES:
        block = data.get(name) or {}
        if not isinstance(block, dict):
            raise ValueError(f"{name} must be an object")
        if block.get("status") != "CONFIRMED":
            continue
        if not block.get("source") or not sourced(block["source"]):
            raise ValueError(f"Confirmed {name} needs a current source URL")
        required = {"coupon": ("code", "benefit_text", "terms", "valid_from", "valid_until"),
                    "discovery": ("title", "body"), "brand": ("title", "body"), "line": ("url",)}[name]
        if any(not isinstance(block.get(key), str) or not block[key].strip() for key in required):
            raise ValueError(f"Confirmed {name} is missing required current content")
        if name == "coupon":
            if block.get("channel") != data.get("channel", "amazon"):
                raise ValueError("Coupon channel differs from email destination")
            try:
                start, end = date.fromisoformat(block["valid_from"]), date.fromisoformat(block["valid_until"])
            except ValueError as error:
                raise ValueError("Coupon dates must be exact ISO dates") from error
            if end < start:
                raise ValueError("Coupon expiry precedes its start")
        if block.get("url"):
            if not sourced(block["url"]):
                raise ValueError(f"Confirmed {name} needs a current destination URL")
        if name == "discovery" and block.get("product"):
            product = block["product"]
            if (not isinstance(product, dict) or not isinstance(product.get("id"), str)
                    or not re.fullmatch(r"[a-z][a-z0-9_]*", product["id"])
                    or product.get("asset_product_id") != product["id"]):
                raise ValueError("Discovery product asset must be bound to its exact product id")
            for key in ("name", "image", "image_source", "product_source"):
                if not product.get(key):
                    raise ValueError(f"Discovery product is missing {key}")
            resource(product["image"])
            if not sourced(product["image_source"]) or not sourced(product["product_source"]):
                raise ValueError("Discovery product needs current official asset and product sources")
            destination(product.get("image_url"), "ASSET_" + product["id"].upper() + "_URL")
        if name == "line" and block.get("qr_image"):
            if block.get("qr_target") != block["url"]:
                raise ValueError("LINE QR target must exactly match the confirmed LINE URL")
            qr_path = Path(block["qr_image"])
            resource(qr_path)
            if not qr_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("LINE QR image must be a PNG")
            destination(block.get("qr_image_url"), "ASSET_LINE_QR_URL")


def validate_input(data, plan):
    if plan.get("planning_status") != "READY_FOR_INTERNAL_RENDER":
        raise ValueError("BLOCKED_HISTORY_EVIDENCE: a ready history plan is required")
    recipe = plan.get("selected_recipe", {})
    rid = recipe.get("id")
    if rid not in SUPPORTED or recipe.get("card_layout") != SUPPORTED[rid]:
        raise ValueError("BLOCKED_RUNTIME_SCOPE: unsupported recipe geometry")
    canonical = next(r for r in json.loads(CATALOG.read_text())["recipes"] if r["id"] == rid)
    if any(recipe.get(key) != canonical.get(key) for key in ('id', 'hero_style', 'card_layout', 'modules', 'tokens', 'source_refs', 'primary_source_ref', 'module_treatments')):
        raise ValueError("Recipe differs from the versioned catalog; create a reviewed candidate recipe instead")
    if plan.get("visual_inheritance") != "EVIDENCE_BACKED_CANDIDATE":
        raise ValueError("Visual evidence is required; a template label alone is insufficient")
    references = plan.get('selected_reference_ids', [])
    evidence_hashes = plan.get('source_image_hashes', [])
    covered = {item.get('reference_id') for item in evidence_hashes
               if isinstance(item, dict) and re.fullmatch(r'[a-f0-9]{64}', str(item.get('sha256', '')))
               and isinstance(item.get('bytes'), int) and item['bytes'] > 0}
    if (not references or canonical['primary_source_ref'] not in references
            or not set(references).issubset(set(canonical['source_refs']))
            or not set(references).issubset(covered)):
        raise ValueError('BLOCKED_HISTORY_EVIDENCE: selected references need their image hash records')
    for key in ("subject", "preheader", "hero_title", "campaign_name", "main_cta"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"Missing copy: {key}")
    if "ここにプレヘッダー" in data["preheader"]:
        raise ValueError("Historical placeholder preheader must not be inherited")
    products = data.get("products", [])
    context = plan.get('campaign_context', {})
    if (context.get('channel') not in canonical['channels']
            or context.get('campaign_type') not in canonical['campaign_types']
            or context.get('stage') not in canonical['stages']
            or context.get('product_count') != len(products)):
        raise ValueError('Current render input does not match the planned campaign scope')
    if data.get('channel', context['channel']) != context['channel']:
        raise ValueError('Current destination channel differs from the plan')
    lo, hi = canonical["product_range"]
    if not lo <= len(products) <= hi:
        raise ValueError("Product count is outside this recipe scope")
    ids = [p.get("id") for p in products]
    if len(ids) != len(set(ids)) or any(not isinstance(i, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", i) for i in ids):
        raise ValueError("Each product needs a unique stable id")
    for product in products:
        for key in ("name", "benefit", "image", "image_source", "product_source"):
            if not product.get(key):
                raise ValueError(f"Missing {key} for {product['id']}")
        if product.get("asset_product_id") != product["id"]:
            raise ValueError("Official product asset must be bound to the same product id")
        resource(product["image"])
        for key in ("image_source", "product_source"):
            destination(product[key], "UNUSED")
        destination(product.get("url"), product["id"].upper() + "_URL")
        destination(product.get("image_url"), "ASSET_" + product["id"].upper() + "_URL")
        offer_state(product.get("offer") or {}, context["channel"])
    hero_ids = data.get("hero_product_ids")
    if hero_ids is not None and (not isinstance(hero_ids, list) or not 4 <= len(hero_ids) <= 6
                                 or len(set(hero_ids)) != len(hero_ids) or not set(hero_ids).issubset(ids)):
        raise ValueError("Hero selection needs four to six distinct current product IDs")
    if rid == "autumn-catalog-v1":
        validate_optional_modules(data)
    options = data.get("subject_options", [])
    if options and (not isinstance(options, list) or len(options) != 3
                    or any(not isinstance(option, dict) or not option.get("subject") or not option.get("preheader")
                           for option in options)):
        raise ValueError("Supply exactly three subject/preheader options when options are requested")
    resource(data["logo"])
    if data.get("background"):
        resource(data["background"])
    return canonical


class Email:
    def __init__(self, data, recipe, preview=False):
        self.d, self.r, self.preview = data, recipe, preview
        self.t = recipe["tokens"]
        self.products = data["products"]
        self.shop = 'Amazon' if data.get('channel', 'amazon') == 'amazon' else '公式サイト'
        self.asset_manifest = []

    def editable(self, path, text, tag="span", style="", format_name=None, extra=""):
        fmt = f' data-edit-format="{h(format_name)}"' if format_name else ""
        return f'<{tag} data-edit="{h(path)}"{fmt}{extra} style="{style}">{h(text)}</{tag}>'

    def product_path(self, product):
        return "products." + str(next(i for i, p in enumerate(self.products) if p["id"] == product["id"]))

    def image(self, product, width, klass=""):
        ident = product["id"]
        src = resource(product["image"]) if self.preview else destination(product.get("image_url"), "ASSET_" + ident.upper() + "_URL")
        return f'<img data-product-id="{h(ident)}" class="{klass}" src="{h(src)}" width="{width}" alt="{h(product["name"])}" style="display:block;width:100%;max-width:{width}px;height:auto;margin:0 auto;border:0;">'

    def button(self, label, url=None, token="AMAZON_SALE_URL", secondary=False, edit_label=None, edit_href=None):
        if token == 'AMAZON_SALE_URL' and self.shop != 'Amazon':
            token = 'OFFICIAL_SALE_URL'
        color = self.t["ink"] if secondary else "#ffffff"
        bg = self.t["secondary"] if secondary else self.t["accent"]
        href = destination(url, token)
        attrs = f' data-edit-href="{h(edit_href)}"' if edit_href else ''
        text = self.editable(edit_label, label) if edit_label else h(label)
        return f'<a href="{h(href)}"{attrs} class="button" style="display:block;background:{bg};color:{color};text-decoration:none;text-align:center;font-size:16px;font-weight:700;line-height:1.5;padding:15px 12px;border-radius:30px;">{text} <span aria-hidden="true">→</span></a>'

    def offer(self, p):
        offer = p.get("offer") or {}
        status = offer_state(offer, self.d.get("channel", "amazon"))
        if status:
            price = offer["sale_price_jpy"]
            old = offer.get("reference_price_jpy")
            path = self.product_path(p) + ".offer."
            size = 24 if self.r["card_layout"] == "dense_two_column_catalog" else 27
            text = self.editable(path + "sale_price_jpy", f'¥{price:,}', 'strong', f'font-size:{size}px;color:{self.t["accent"]};white-space:nowrap;', 'jpy', ' class="sale-price"')
            if offer.get("tax_included", status == "CONFIRMED"):
                text += '<span style="font-size:10px;">（税込）</span>'
            if old is not None:
                text += '<br>' + self.editable(path + "reference_price_jpy", f'¥{old:,}', 'del', 'font-size:12px;color:#92949a;', 'jpy', ' class="reference-price"')
            if status == "DRAFT":
                text += '<br><span style="font-size:11px;color:#9b651b;">参考価格・要確認</span>'
            return f'<div data-offer-product="{h(p["id"])}" data-price-status="{status}">{text}</div>'
        price_label = '価格' if self.d.get('campaign_type') == 'product_launch' else 'セール価格'
        if self.r['card_layout'] == 'dense_two_column_catalog':
            path = self.product_path(p) + '.offer.sale_price_jpy'
            editable = self.editable(path, '要確認', 'strong', 'font-size:22px;color:'+self.t['accent']+';', 'jpy', ' class="sale-price"')
            return f'<div data-offer-product="{h(p["id"])}" data-price-status="UNCONFIRMED">{editable}<p style="font-size:11px;line-height:1.6;color:#777;">{price_label}・対象条件を確認中</p></div>'
        return f'<strong style="font-size:13px;line-height:1.6;">{price_label}・対象条件を<br>{self.shop}でチェック</strong>'

    def card(self, p, compact=False, ordinal=None):
        note = f'<p style="font-size:11px;line-height:1.6;color:#777;margin-top:10px;">{h(p.get("note", ""))}</p>' if p.get("note") else ""
        prefix = f'<p style="color:{self.t["accent"]};font-size:12px;font-weight:700;margin-bottom:7px;">{h(p.get("label", "PICK UP"))}</p>'
        product_title = p['name'].removeprefix('SwitchBot ')
        product_title_html = ' '.join('<span style="display:inline-block;">'+h(word)+'</span>' for word in product_title.split())
        text = prefix + f'<p style="font-size:11px;color:#747883;margin-bottom:5px;">SwitchBot</p><h3 style="font-size:{18 if compact else 22}px;line-height:1.5;color:{self.t["ink"]};">{product_title_html}</h3><p style="font-size:14px;line-height:1.75;color:#656975;margin-top:9px;">{h(p["benefit"])}</p>'
        if compact:
            inside = self.image(p, 205) + '<div style="padding-top:15px;">' + text + "</div>"
            commercial = f'<div style="border-top:1px solid #e8e8eb;padding-top:14px;margin-top:15px;margin-bottom:12px;">{self.offer(p)}</div>' + self.button(self.shop+"で見る", p.get("url"), p["id"].upper() + "_URL")
        else:
            inside = f'<table role="presentation" width="100%"><tr><td class="product-image-cell" width="44%" style="width:44%;padding-right:18px;vertical-align:middle;">{self.image(p, 240)}</td><td style="vertical-align:middle;">{text}</td></tr></table>'
            commercial = f'<table role="presentation" width="100%" style="border-top:1px solid #e8e8eb;margin-top:17px;"><tr><td class="commerce-value" style="padding-top:15px;width:47%;vertical-align:middle;">{self.offer(p)}</td><td class="commerce-action" style="padding-top:15px;width:53%;vertical-align:middle;">{self.button(self.shop+"で見る", p.get("url"), p["id"].upper() + "_URL")}</td></tr></table>'
        return f'<div data-card-product="{h(p["id"])}" data-geometry="{"vertical_card" if compact else "image_left_copy_right"}" style="background:#ffffff;border-radius:{self.t["card_radius"]}px;padding:{20 if compact else 24}px;">{inside}{note}{commercial}</div>'

    def catalog_card(self, p):
        path = self.product_path(p)
        name = p["name"].removeprefix("SwitchBot ")
        title = self.editable(path + ".name", name, "h3", "font-size:17px;line-height:1.45;min-height:50px;color:"+self.t["ink"]+";", "strip-switchbot", ' class="catalog-title"')
        benefit = self.editable(path + ".benefit", p["benefit"], "p", "font-size:14px;line-height:1.6;min-height:68px;margin-top:8px;color:#50576a;")
        label = self.editable(path + ".label", p.get("label", ""), "p", "font-size:11px;font-weight:700;line-height:1.5;color:"+self.t["accent"]+";min-height:17px;margin-bottom:6px;", extra=' class="catalog-label"')
        # Reserve the note slot even when empty: image, name, benefit, note and
        # price keep paired purchase buttons aligned without shrinking the copy.
        note = self.editable(path + ".note", p.get("note", ""), "p", "font-size:11px;line-height:1.6;color:#777;min-height:36px;margin-top:6px;", extra=' class="catalog-note"')
        image = '<div class="catalog-image" style="height:184px;margin-bottom:10px;">'+self.image(p, 210, "catalog-product-image")+'</div>'
        action = self.button(self.shop+"で見る", p.get("url"), p["id"].upper()+"_URL", edit_href=path+".url")
        return (f'<div data-card-product="{h(p["id"])}" data-geometry="catalog_two_column_card" class="catalog-card" style="background:#fff;border-radius:16px;padding:16px 14px;">'
                + label + image + title + benefit + note
                + '<div style="border-top:1px solid #ece8e2;padding-top:10px;margin-top:10px;min-height:71px;">'+self.offer(p)+'</div>'
                + '<div style="margin-top:8px;">'+action+'</div></div>')

    def catalog(self):
        body = self.section_label(self.d.get("catalog_heading", "注目のセール対象製品"), self.d.get("catalog_caption", "気になる便利を、まとめてチェック。"))
        for i in range(0, len(self.products), 2):
            pair = self.products[i:i+2]
            cards = [f'<td class="catalog-cell" width="49%" style="width:49%;vertical-align:top;">{self.catalog_card(p)}</td>' for p in pair]
            if len(cards) == 1:
                cards.append('<td class="catalog-cell" width="49%" style="width:49%;"></td>')
            body += '<table role="presentation" width="100%" data-geometry="catalog_two_column" style="table-layout:fixed;"><tr>'+cards[0]+'<td class="catalog-gap" width="2%" style="width:2%;"></td>'+cards[1]+'</tr></table><div style="height:12px;"></div>'
        return body

    def optional_visible(self, name):
        if self.d.get("module_enabled", {}).get(name) is False:
            return False
        return self.preview or name == "brand" or (self.d.get(name) or {}).get("status") == "CONFIRMED"

    def optional_module(self, name):
        block = self.d.get(name) or {}
        confirmed = block.get("status") == "CONFIRMED"
        if not self.optional_visible(name):
            return ""
        if name == "coupon":
            benefit = block.get("benefit_text") if confirmed else "クーポン特典を準備中"
            code = block.get("code") if confirmed else "要確認"
            terms = block.get("terms") if confirmed else "特典内容・対象商品・有効期間・適用条件は確定後に反映します。"
            body = self.section_label("このメールをご覧の方へ")
            body += '<div style="background:#ff554d;color:#fff;border:2px dashed #fff4e6;border-radius:18px;padding:25px 20px;text-align:center;">'
            body += self.editable("coupon.benefit_text", benefit, "h2", "font-size:28px;line-height:1.5;")
            body += '<p style="font-size:13px;margin:13px 0 6px;">クーポンコード</p>'+self.editable("coupon.code", code, "p", "font-size:26px;font-weight:800;letter-spacing:1px;")+'</div>'
            body += self.editable("coupon.terms", terms, "p", "font-size:12px;line-height:1.8;margin-top:12px;text-align:center;color:#777;")
            if confirmed:
                body += '<p style="font-size:12px;text-align:center;margin-top:8px;">'+h(block["valid_from"])+" ～ "+h(block["valid_until"])+"</p>"
            else:
                body += '<p style="font-size:11px;color:#9b651b;text-align:center;margin-top:8px;">社内確認用の仮枠・送信用 HTML には未掲載</p>'
        elif name == "discovery":
            title = block.get("title") if confirmed else "新しい便利もチェック"
            body_text = block.get("body") if confirmed else "この秋にご紹介する製品と、Amazonでの販売状況を確認中です。"
            body = '<div style="background:#fff;border-radius:18px;padding:24px;">'+self.editable("discovery.title", title, "h2", "font-size:25px;line-height:1.5;color:"+self.t["accent"]+";")
            product = block.get("product") if confirmed else None
            if product:
                body += '<table role="presentation" width="100%" data-geometry="discovery_image_left" style="margin-top:17px;"><tr><td width="38%" style="width:38%;vertical-align:middle;padding-right:15px;">'+self.image(product,170)+'</td><td style="vertical-align:middle;">'
                body += self.editable("discovery.product.name", product["name"], "h3", "font-size:17px;line-height:1.6;")
            body += self.editable("discovery.body", body_text, "p", "font-size:14px;line-height:1.8;margin-top:12px;")
            if product:
                body += '</td></tr></table>'
            if confirmed and block.get("url"):
                body += '<div style="margin-top:18px;">'+self.button(block.get("cta", "Amazonでチェック"), block["url"], edit_label="discovery.cta", edit_href="discovery.url")+'</div>'
            if not confirmed:
                body += '<p style="font-size:11px;color:#9b651b;margin-top:10px;">社内確認用・対象製品とリンクは要確認</p>'
            body += '</div>'
        elif name == "brand":
            title = block.get("title") if confirmed else "暮らしに、ちょうどいい便利を。"
            body_text = block.get("body") if confirmed else "SwitchBot"
            body = '<div style="background:#252947;color:#fff;border-radius:18px;padding:30px 22px;text-align:center;">'+self.editable("brand.title", title, "h2", "font-size:25px;line-height:1.5;")
            body += self.editable("brand.body", body_text, "p", "font-size:14px;line-height:1.8;margin-top:12px;")+'</div>'
        else:
            body = self.section_label("LINEでも、最新情報を。")
            body_text = block.get("body", "SwitchBotの製品情報やお知らせをお届けします。") if confirmed else "公式LINEの友だち追加リンクを確認中です。"
            body += self.editable("line.body", body_text, "p", "font-size:14px;line-height:1.8;text-align:center;margin-bottom:15px;")
            if confirmed:
                if block.get("qr_image"):
                    qr_src = resource(block["qr_image"]) if self.preview else destination(block.get("qr_image_url"),"ASSET_LINE_QR_URL")
                    body += f'<a href="{h(block["url"])}" data-edit-href="line.url" style="display:block;margin:0 auto 18px;text-align:center;"><img src="{h(qr_src)}" data-qr-target="{h(block["qr_target"])}" width="126" height="126" alt="SwitchBot LINE公式アカウントの友だち追加QRコード" style="display:block;width:126px;height:126px;margin:0 auto;border:0;"></a>'
                action = self.button(block.get("cta", "LINE公式アカウントをチェック"), block["url"], edit_label="line.cta", edit_href="line.url")
                body += action.replace('background:'+self.t['accent']+';', 'background:#06c755;', 1)
            else:
                body += '<div style="background:#e9f7ec;color:#31723f;border:1px dashed #83bd90;border-radius:24px;padding:15px;text-align:center;font-size:14px;font-weight:700;">友だち追加リンク：要確認</div>'
        return f'<td class="section-pad" style="padding:25px 24px 8px;background:{self.t["paper"]};">{body}</td>'

    def hero(self, scenario=False, single=False):
        style = self.r["hero_style"]
        dark = style in {"commerce_burst", "security_scenario"}
        color = "#ffffff" if dark else self.t["accent"] if style == "autumn_festival" else self.t["ink"]
        bg = self.t["hero"]
        logo_src = resource(self.d["logo"]) if self.preview else destination(self.d.get("logo_url"), "ASSET_LOGO_URL")
        background = ""
        if self.d.get("background") and style == "autumn_festival":
            url = resource(self.d["background"]) if self.preview else destination(self.d.get("background_url"), "ASSET_BACKGROUND_URL")
            background = f"background-image:url('{h(url)}');background-size:cover;background-position:center;"
        date = self.d.get("period_text", "")
        date_html = self.editable("period_text", date, "p", f'display:inline-block;background:#fff7e9;color:{self.t["accent"]};padding:9px 18px;border-radius:28px;font-size:19px;font-weight:700;margin:15px 0;') if date else ""
        label = self.d.get("hero_kicker", self.shop+"でスタート")
        hero_default = self.products[:4] if self.r["card_layout"] == "dense_two_column_catalog" else self.products
        hero_ids = self.d.get("hero_product_ids", [p["id"] for p in hero_default])
        hero_products = [next(p for p in self.products if p["id"] == ident) for ident in hero_ids]
        family = self.image(self.products[0], 350) if single else '<table role="presentation" width="100%" style="background:#ffffff;border-radius:20px;"><tr>' + "".join(f'<td style="width:{100/len(hero_products):.3f}%;padding:8px 3px;vertical-align:middle;">{self.image(p, 120, "family-image")}</td>' for p in hero_products) + "</tr></table>"
        heading = self.d["hero_title"] if scenario or single else self.d["campaign_name"]
        sub = self.d.get("hero_support", self.d["hero_title"])
        heading_path = "hero_title" if scenario or single else "campaign_name"
        sub_path = "hero_support" if self.d.get("hero_support") else "hero_title"
        return f'<td align="center" class="hero-pad" style="padding:24px 30px 28px;background-color:{bg};{background}color:{color};"><img src="{h(logo_src)}" width="136" alt="SwitchBot" style="display:block;width:136px;height:auto;margin:0 auto 22px;"><p data-edit="hero_kicker" style="font-size:17px;line-height:1.5;font-weight:700;">{h(label)}</p><h1 data-edit="{heading_path}" class="hero-heading" style="font-size:43px;line-height:1.35;letter-spacing:-1px;margin-top:11px;font-weight:800;color:{color};white-space:pre-line;">{h(heading)}</h1><p data-edit="{sub_path}" style="font-size:16px;line-height:1.7;font-weight:700;margin-top:13px;">{h(sub)}</p>{date_html}<div style="margin:8px 0 18px;">{self.button(self.d["main_cta"], self.d.get("main_url"), secondary=dark, edit_label="main_cta", edit_href="main_url")}</div><div class="hero-product-family">{family}</div><p data-edit="hero_footnote" style="font-size:11px;margin-top:10px;color:{color};">{h(self.d.get("hero_footnote", "対象商品・販売条件は商品ページでご確認ください。"))}</p></td>'

    def section_label(self, title, caption=""):
        return f'<h2 style="font-size:25px;line-height:1.5;color:{self.t["accent"]};text-align:center;margin-bottom:19px;">{h(title)}</h2>' + (f'<p style="font-size:13px;line-height:1.8;color:#6a6a70;text-align:center;margin:-9px 0 20px;">{h(caption)}</p>' if caption else "")

    def module(self, name):
        if name in {"campaign_hero", "scenario_hero", "product_hero"}:
            return self.hero(scenario=name == "scenario_hero", single=name == "product_hero")
        if name in OPTIONAL_MODULES:
            return self.optional_module(name)
        body = ""
        if name == "product_catalog":
            body = self.catalog()
        elif name == "featured_product":
            body = self.section_label(self.d.get("featured_heading", "この秋、まずチェックしたい一台。")) + self.card(self.products[0])
        elif name == "featured_products":
            body = self.section_label(self.d.get("featured_heading", "今回チェックしたいアイテム")) + '<div style="height:18px;"></div>'.join(self.card(p) for p in self.products[:2])
        elif name == "secondary_products":
            start = 2 if self.r["card_layout"] == "priority_split_then_grid" else 1
            other = self.products[start:]
            if not other:
                return '<td style="height:0;"></td>'
            body = self.section_label(self.d.get("secondary_heading", "暮らしに合わせて、選ぼう。"))
            for i in range(0, len(other), 2):
                pair = other[i:i+2]
                if len(pair) == 1:
                    body += self.card(pair[0])
                else:
                    body += f'<table role="presentation" width="100%" data-geometry="secondary_two_column"><tr><td class="grid-card" width="48.5%" style="width:48.5%;vertical-align:top;">{self.card(pair[0],True)}</td><td class="grid-gap" width="3%" style="width:3%;"></td><td class="grid-card" width="48.5%" style="width:48.5%;vertical-align:top;">{self.card(pair[1],True)}</td></tr></table>'
                body += '<div style="height:16px;"></div>'
        elif name == "scenario_products":
            body = self.section_label(self.d.get("featured_heading", "気になる場所から、選ぶ。")) + '<div style="height:18px;"></div>'.join(self.card(p) for p in self.products)
        elif name == "selection_help":
            body = '<h2 style="font-size:22px;line-height:1.6;">購入前に、設置条件をチェック。</h2><p style="font-size:15px;line-height:1.8;margin-top:10px;">取り付け場所、対応機器、セット内容は、各商品ページでご確認ください。</p>'
        elif name == "value_story":
            p = self.products[0]
            body = self.section_label(self.d.get("story_heading", "毎日の暮らしに、こんな便利を。")) + f'<p style="font-size:19px;line-height:1.9;">{h(p["benefit"])}</p>'
        elif name == "product_details":
            details = self.d.get("details", [])
            if not details:
                body = f'<p style="font-size:14px;line-height:1.9;">{h(self.products[0].get("note", "セット内容・対応条件は商品ページでご確認ください。"))}</p>'
            else:
                body = self.section_label("使う前に、知っておきたいこと。")
                for detail in details:
                    if not detail.get("source") or detail.get("status") != "CONFIRMED":
                        continue
                    body += f'<h3 style="font-size:20px;margin:20px 0 8px;">{h(detail["title"])}</h3><p style="font-size:15px;line-height:1.8;">{h(detail["body"])}</p>'
        elif name == "closing_cta":
            return f'<td align="center" class="section-pad" style="padding:29px;background:{self.t["accent"]};color:#ffffff;"><p data-edit="campaign_name" style="font-size:13px;line-height:1.5;">{h(self.d["campaign_name"])}</p><h2 data-edit="closing_heading" style="font-size:25px;line-height:1.6;margin:10px 0 18px;">{h(self.d.get("closing_heading", "暮らしに合う便利を、"+self.shop+"で。"))}</h2>{self.button(self.d["main_cta"],self.d.get("main_url"),secondary=True,edit_label="main_cta",edit_href="main_url")}</td>'
        elif name == "legal_footer":
            body = '<p style="font-size:11px;line-height:1.9;color:#777;">※対象商品・価格・販売条件は、商品ページでご確認ください。<br>※商品によって必要な機器や設置条件が異なります。</p><p style="font-size:12px;line-height:1.8;margin-top:19px;">SWITCHBOT株式会社</p>'
            body += f'<p style="font-size:11px;line-height:1.8;margin-top:10px;"><a href="{h(destination(self.d.get("preferences_url"), "PREFERENCES_URL"))}">配信設定</a>　｜　<a href="{h(destination(self.d.get("unsubscribe_url"), "UNSUBSCRIBE_URL"))}">配信停止</a></p>'
        else:
            raise ValueError("Unsupported recipe module: " + name)
        return f'<td class="section-pad" style="padding:27px 24px 8px;background:{self.t["paper"]};">{body}</td>'

    def render(self):
        base = f'html,body{{margin:0;padding:0;background:{self.t["paper"]};width:100%;}}body,table,td,a{{font-family:"Noto Sans JP","Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,Arial,sans-serif;}}table{{border-collapse:collapse;border-spacing:0;}}td{{padding:0;}}p,h1,h2,h3{{margin:0;}}*{{box-sizing:border-box;}}img{{border:0;}}.email-canvas{{width:100%;max-width:600px;}}'
        mobile = '.hero-pad{padding:22px 20px!important;}.hero-heading{font-size:34px!important;}.section-pad{padding:23px 16px 7px!important;}.button{font-size:14px!important;padding:13px 10px!important;}.grid-card{display:block!important;width:100%!important;}.grid-gap{display:block!important;width:100%!important;height:16px!important;}.commerce-value,.commerce-action{display:block!important;width:100%!important;text-align:center;}.product-image-cell{width:40%!important;padding-right:11px!important;}'
        narrow = '.hero-heading{font-size:30px!important;}.product-image-cell{display:block!important;width:100%!important;padding:0 0 14px!important;}'
        if self.r["card_layout"] == "dense_two_column_catalog":
            base += '.catalog-product-image{height:184px!important;max-height:184px;object-fit:contain;}.catalog-card .button{background:#252947!important;font-size:14px;padding:12px 6px;min-height:45px;}.catalog-card{break-inside:avoid;}'
            mobile += '.catalog-cell{display:table-cell!important;width:49%!important;}.catalog-gap{display:table-cell!important;width:2%!important;}.catalog-card{padding:12px 10px!important;}.catalog-image{height:134px!important;}.catalog-product-image{height:134px!important;max-height:134px!important;}.catalog-card h3{font-size:16px!important;}.catalog-title{min-height:70px!important;}.catalog-label{min-height:34px!important;}.catalog-note{min-height:53px!important;}.catalog-card .button{font-size:13px!important;padding:12px 5px!important;}.catalog-card .sale-price{font-size:23px!important;}.catalog-card .reference-price{font-size:11px!important;}'
            narrow += '.catalog-cell{display:block!important;width:100%!important;}.catalog-gap{display:block!important;width:100%!important;height:12px!important;}'
        preheader = f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all;">{h(self.d["preheader"])}</div>'
        rows = ''.join(f'<tr data-module="{name}">{body}</tr>' for name in self.r["modules"] if (body := self.module(name)))
        notice = '<tr><td style="background:#20283d;color:white;text-align:center;font-size:10px;padding:7px;">社内確認用｜日程・価格・リンクは未確定</td></tr>' if self.preview else ''
        markup = f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="x-apple-disable-message-reformatting"><meta name="edm-preheader" content="{h(self.d["preheader"])}"><title data-edit="subject">{h(self.d["subject"])}</title><style>{base}@media screen and (max-width:480px){{{mobile}}}@media screen and (max-width:340px){{{narrow}}}</style></head><body data-status="INTERNAL_DRAFT" data-recipe="{self.r["id"]}">{preheader}<table role="presentation" width="100%"><tr><td align="center"><table class="email-canvas" role="presentation" width="600" style="width:100%;max-width:600px;" align="center">{notice}{rows}</table></td></tr></table></body></html>'
        return markup, mobile


def embed_font(markup, font_path):
    if not font_path:
        return markup
    from fontTools import subset
    font = subset.load_font(font_path, subset.Options())
    chars = re.sub(r'<[^>]+>', '', markup) + 'オフライン組版参考ブラウザーメール実機検証未実施'
    sub = subset.Subsetter()
    sub.populate(text=html.unescape(chars))
    sub.subset(font)
    data = io.BytesIO()
    font.flavor = 'woff'
    font.save(data)
    encoded = base64.b64encode(data.getvalue()).decode()
    rule = f"@font-face{{font-family:'Noto Sans JP';src:url('data:font/woff;base64,{encoded}') format('woff');font-weight:100 900;}}"
    return markup.replace('<style>', '<style>' + rule, 1)


def offline_export(markup, mobile_css, out):
    import fitz
    import weasyprint
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    try:
        from weasyprint.urls import URLFetcher
        fetch_data = URLFetcher(allowed_protocols=['data'], fail_on_errors=True)
    except ImportError:
        from weasyprint import default_url_fetcher
        fetch_data = default_url_fetcher

    def data_only(url, *args, **kwargs):
        if not url.startswith('data:'):
            raise ValueError('Offline typesetting permits embedded assets only')
        return fetch_data(url)

    exports = []
    for label, width in [('desktop', 600), ('mobile', 390)]:
        font = FontConfiguration()
        css = f'@page{{size:{width}px 16000px;margin:0;}}html,body{{width:{width}px!important;}}' + (mobile_css if width < 481 else '')
        version = markup.replace('<body ', '<body ', 1)
        version = re.sub(r'(<body[^>]*>)', r'\1<div style="background:#171c29;color:white;padding:7px 8px;text-align:center;font-size:9px;">オフライン組版参考｜ブラウザー・メール実機検証未実施</div>', version, count=1)
        doc = HTML(string=version, url_fetcher=data_only).render(stylesheets=[CSS(string=css,font_config=font)],font_config=font,presentational_hints=True)
        if len(doc.pages) != 1:
            raise ValueError('Offline preview exceeds one reference canvas')
        boxes = list(doc.pages[0]._page_box.descendants())
        body = [b for b in boxes if getattr(b,'element_tag',None)=='body']
        bottom = max(b.position_y+b.margin_height() for b in body)+2
        pdf = fitz.open(stream=doc.write_pdf(),filetype='pdf')
        page = pdf[0]
        page.set_cropbox(fitz.Rect(0,0,width*.75,min(page.rect.height,bottom*.75)))
        pix = page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
        output = out / f'{label}-preview.png'
        pix.save(output)
        exports.append({'file':output.name,'width_css_px':width,'height_css_px':round(bottom),'png_width':pix.width,'png_height':pix.height,'sha256':digest(output.read_bytes())})
        if label == 'desktop':
            # A first-screen excerpt of the HTML typesetting, not an AI email mockup.
            hero = next((b for b in boxes if getattr(b,'element',None) is not None and b.element.get('data-module') in {'campaign_hero','scenario_hero','product_hero'}),None)
            if hero is not None:
                clip = fitz.Rect(0,max(0,hero.position_y*.75),width*.75,min(page.rect.height,(hero.position_y+hero.height)*.75))
                page.get_pixmap(matrix=fitz.Matrix(2,2),clip=clip,alpha=False).save(out/'hero-preview.png')
    return {'status':'OFFLINE_REFERENCE_ONLY','renderer':'WeasyPrint','renderer_version':weasyprint.__version__,'javascript':False,'network':False,'browser_screenshot':False,'mobile_css_explicitly_applied':True,'outputs':exports}


def render_review_parts(data, plan):
    """Return the same native/preview pair used for editing and offline rendering."""
    recipe = validate_input(data,plan)
    data = dict(data, channel=plan['campaign_context']['channel'], campaign_type=plan['campaign_context']['campaign_type'])
    email, _ = Email(data,recipe).render()
    preview, mobile = Email(data,recipe,True).render()
    preview = embed_font(preview,data.get('font_file'))
    return {'email':email, 'preview':preview, 'mobile_css':mobile, 'recipe':recipe, 'data':data}


def build(data, plan, out, export=True):
    parts = render_review_parts(data, plan)
    email, preview, mobile, recipe, data = (parts[k] for k in ('email','preview','mobile_css','recipe','data'))
    out = Path(out)
    out.mkdir(parents=True,exist_ok=True)
    (out/'email.html').write_text(email,encoding='utf-8')
    (out/'email-preview.html').write_text(preview,encoding='utf-8')
    modules = re.findall(r'<tr data-module="([^"]+)',email)
    cards = re.findall(r'data-card-product="([^"]+)',email)
    required_cards = [] if recipe['card_layout']=='single_product_story' else [p['id'] for p in data['products']]
    expected_modules = [name for name in recipe['modules'] if name not in OPTIONAL_MODULES or Email(data,recipe).optional_visible(name)]
    checks = {'recipe_module_order':modules==expected_modules,'exact_product_cards':cards==required_cards,'script_free_email':'<script' not in email,'no_data_images_in_email':'data:image/' not in email,'subject_preserved':h(data['subject']) in email,'preheader_preserved':h(data['preheader']) in email,'all_image_alt':all('alt="' in tag for tag in re.findall(r'<img\b[^>]*>',email)),'no_historical_placeholder':'ここにプレヘッダー' not in email}
    if not all(checks.values()):
        raise ValueError('Static renderer contract failed: '+str(checks))
    refs = plan.get('selected_reference_ids',[])
    export_report = {'status':'NOT_EXECUTED'}
    if export:
        try:
            export_report = offline_export(preview,mobile,out)
        except (ImportError,ValueError,OSError) as error:
            export_report={'status':'BLOCKED_OFFLINE_RENDER','reason':str(error)}
    write_json(out/'offline-render.json',export_report)
    tokens = sorted(set(TOKEN.findall(email)))
    asset_records = [{'product_id':p['id'],'filename':Path(p['image']).name,'sha256':digest(Path(p['image']).read_bytes()),'image_source':p['image_source'],'product_source':p['product_source']} for p in data['products']]
    discovery = data.get('discovery') or {}
    if discovery.get('status') == 'CONFIRMED' and discovery.get('product'):
        p = discovery['product']
        asset_records.append({'product_id':p['id'],'module':'discovery','filename':Path(p['image']).name,
                              'sha256':digest(Path(p['image']).read_bytes()),'image_source':p['image_source'],'product_source':p['product_source']})
    line = data.get('line') or {}
    if line.get('status') == 'CONFIRMED' and line.get('qr_image'):
        asset_records.append({'module':'line','role':'qr_code','filename':Path(line['qr_image']).name,
                              'sha256':digest(Path(line['qr_image']).read_bytes()),'target_url':line['qr_target'],
                              'source':line['source'],'scope':'PNG asset and declared target binding verified; QR decoding is a separate check.'})
    source_map = {'recipe_id':recipe['id'],'source_reference_ids':refs,'observed_features':recipe['observed_features'],'controlled_adaptations':recipe['controlled_adaptations'],'forbidden_inheritance':recipe['forbidden_inheritance'],'modules':modules,'module_mapping':plan.get('module_mapping',[]),'geometry':recipe['card_layout'],'scope':'Analyst-observed visual features, not measured pixel similarity or human approval'}
    write_json(out/'inheritance-map.json',source_map)
    write_json(out/'asset-manifest.json',asset_records)
    price_sources = [{'product_id':p['id'], 'status':(p.get('offer') or {}).get('status','UNCONFIRMED'),
                      'source':(p.get('offer') or {}).get('source'), 'channel':(p.get('offer') or {}).get('channel'),
                      'rendered_price_status':offer_state(p.get('offer') or {},data['channel'])}
                     for p in data['products']]
    write_json(out/'price-source-manifest.json',price_sources)
    browser = {'status':'NOT_EXECUTED','tested_widths':[], 'reason':'This adapter does not execute browser QA.'}
    if data.get('browser_qa', {}).get('status') == 'BLOCKED':
        browser = {'status':'BLOCKED','tested_widths':[], 'reason':str(data['browser_qa'].get('reason','Browser unavailable in current environment'))}
    report = {'status':'INTERNAL_DRAFT','static_qa':'PASS','static_checks':checks,'send_readiness':'BLOCKED','unresolved_tokens':tokens,'browser_qa':browser,'email_client_qa':'NOT_EXECUTED','esp_test_send':'NOT_EXECUTED','named_human_approval':'NOT_PROVIDED','native_email_bytes':len(email.encode()),'email_sha256':digest(email.encode()),'preview_sha256':digest(preview.encode()),'offline_render':export_report,'recipe_id':recipe['id'],'runtime':'portable-history-adapter','frozen_ruby_runtime_executed':False}
    report['draft_price_product_ids'] = [p['id'] for p in data['products'] if offer_state(p.get('offer') or {},data['channel']) == 'DRAFT']
    report['price_source_gaps'] = [p['id'] for p in data['products'] if offer_state(p.get('offer') or {},data['channel']) is None]
    report['optional_modules_omitted_from_native'] = [name for name in recipe['modules'] if name in OPTIONAL_MODULES and name not in modules]
    report['commercial_blockers'] = (['DRAFT_PRICES_REQUIRE_APPROVAL'] if report['draft_price_product_ids'] else []) + (['CURRENT_PRICES_MISSING'] if report['price_source_gaps'] else [])
    report['preview_module_order'] = re.findall(r'<tr data-module="([^"]+)',preview)
    write_json(out/'qa-report.json',report)
    write_json(out/'plan.json',plan)
    copy = '# 件名\n'+data['subject']+'\n\n# Preheader\n'+data['preheader']+'\n\n# Hero\n'+data['hero_title']+'\n\n'
    if data.get('subject_options'):
        copy += '# 件名・プレビュー文の候補\n\n'
        copy += '\n\n'.join(f'{index+1}. {option.get("label", "候補")}\n件名：{option["subject"]}\nプレビュー文：{option["preheader"]}'
                            for index,option in enumerate(data['subject_options']))+'\n\n'
    copy += '\n\n'.join(p['name']+'\n'+p['benefit'] for p in data['products'])
    (out/'copy-ja.md').write_text(copy,encoding='utf-8')
    ref_list=''.join('<li>'+h(x)+'</li>' for x in refs)
    feature_list=''.join('<li>'+h(x)+'</li>' for x in recipe['observed_features'])
    preview_uri='data:text/html;base64,'+base64.b64encode(preview.encode()).decode()
    review=f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>秋促 EDM · 历史模板重制</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#f5f1e9;color:#273043;font-family:Arial,sans-serif}}header{{padding:25px;background:white;border-bottom:4px solid #ff5731}}h1{{font-size:24px;margin:0 0 10px}}.layout{{display:grid;grid-template-columns:320px minmax(0,1fr);gap:24px;padding:24px;max-width:1100px;margin:auto}}aside{{background:white;padding:22px;align-self:start;border-radius:14px}}aside p,aside li{{font-size:13px;line-height:1.8}}aside ul{{padding-left:18px}}.frame{{width:600px;max-width:100%;margin:auto}}iframe{{width:100%;height:5400px;border:0;background:white}}button{{padding:10px 18px;margin:0 8px 12px 0;background:#ff5731;border:0;border-radius:22px;color:white;cursor:pointer}}@media(max-width:800px){{.layout{{grid-template-columns:1fr;padding:12px}}}}</style></head><body><header><h1>秋促开售 EDM｜依据历史邮件重制</h1><div>内部审阅候选 · 历史事实未继承 · 当前链接及优惠待配置</div></header><main class="layout"><aside><h2>邮件任务</h2><p>{h(data["subject"])}</p><p>{h(data["preheader"])}</p><h2>本次参考</h2><ul>{ref_list}</ul><h2>实际继承</h2><ul>{feature_list}</ul><h2>验证范围</h2><p>HTML 静态检查通过。PNG 为同份 HTML 的离线排版图，未执行浏览器或邮件客户端验证。</p><h2>发送前待补</h2><p>活动日期和 SKU、价格与优惠条件、Amazon 链接、素材 HTTPS 托管、退订和发件信息、测试发送及最终审核。</p></aside><section><button type="button" data-width="600">桌面 600</button><button type="button" data-width="390">手机 390</button><div class="frame"><iframe title="日本 EDM 审阅" sandbox="" src="{preview_uri}"></iframe></div></section></main><script>document.querySelectorAll("[data-width]").forEach(b=>b.addEventListener("click",()=>{{document.querySelector(".frame").style.width=b.dataset.width+"px";}}));</script></body></html>'
    (out/'review.html').write_text(review,encoding='utf-8')
    editor_path = ROOT / 'scripts' / 'editable_review.py'
    if editor_path.is_file():
        import importlib.util
        spec = importlib.util.spec_from_file_location('edm_editable_review',editor_path)
        editor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(editor)
        editor_preview = preview
        editor_email = email
        if any(enabled is False for enabled in data.get('module_enabled',{}).values()):
            # Keep hidden optional rows available inside the editor so they can be
            # re-enabled. The normal preview/PNG still follows module_enabled.
            editor_preview, _ = Email(dict(data,module_enabled={}),recipe,True).render()
            editor_preview = embed_font(editor_preview,data.get('font_file'))
            editor_email, _ = Email(dict(data,module_enabled={}),recipe).render()
        editor.build_editor(data,editor_preview,editor_email,out/'editable-review.html')
    qa_md='# 发送前检查\n\n内部审阅稿。静态 HTML QA PASS；发送 BLOCKED。\n\n- 历史参考：'+', '.join(refs)+'\n- 版式：'+recipe['id']+'\n- 已检查模块顺序和独立 SKU/图片绑定；没有测量历史图片相似百分比。\n- 离线长图：'+export_report['status']+'；来自当前 HTML 的排版，不是 image_gen 画出的邮件。\n- 浏览器、邮件客户端和 ESP 发送未完成。\n- 尚未替换变量：'+', '.join(tokens)+'\n- 日期、优惠、素材使用、发件与退订配置及最终人工审核仍需完成。\n'
    (out/'qa-report.md').write_text(qa_md,encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True)
    parser.add_argument('--plan',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--skip-offline-preview',action='store_true')
    args=parser.parse_args()
    try:
        input_path=Path(args.input).resolve()
        data=json.loads(input_path.read_text())
        for key in ('logo','background','font_file'):
            if data.get(key) and not Path(data[key]).is_absolute():
                data[key]=str(input_path.parent/data[key])
        for product in data.get('products',[]):
            if product.get('image') and not Path(product['image']).is_absolute():
                product['image']=str(input_path.parent/product['image'])
        discovery_product = (data.get('discovery') or {}).get('product') or {}
        if discovery_product.get('image') and not Path(discovery_product['image']).is_absolute():
            discovery_product['image'] = str(input_path.parent/discovery_product['image'])
        line = data.get('line') or {}
        if line.get('qr_image') and not Path(line['qr_image']).is_absolute():
            line['qr_image'] = str(input_path.parent/line['qr_image'])
        plan=json.loads(Path(args.plan).read_text())
        report=build(data,plan,Path(args.out),not args.skip_offline_preview)
        print(json.dumps({k:report[k] for k in ('status','static_qa','send_readiness','recipe_id','native_email_bytes')},ensure_ascii=False))
        return 0
    except (ValueError,KeyError,OSError,StopIteration) as error:
        print(json.dumps({'status':'BLOCKED_RENDER','reason':str(error)},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
