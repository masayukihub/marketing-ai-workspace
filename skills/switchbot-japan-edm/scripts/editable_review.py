#!/usr/bin/env python3
"""Build a local, self-contained editor around the actual rendered EDM HTML.

The editor changes bound text, HTTPS destinations and optional module visibility.
It exports the native email separately from the image-embedded review. Edits never
approve prices or claims, and PNGs must be re-created by the HTML renderer.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


EDITOR_JS = r'''
(function () {
  'use strict';
  const BLOCKED_KEYS = new Set(['__proto__', 'constructor', 'prototype']);
  const OPTIONAL_MODULES = new Set(['discovery', 'coupon', 'brand', 'line']);
  const clone = value => JSON.parse(JSON.stringify(value));
  const parts = path => {
    const keys = String(path).split('.');
    if (!keys.length || keys.some(key => !/^[A-Za-z0-9_]+$/.test(key) || BLOCKED_KEYS.has(key))) throw new Error('无效的字段路径');
    return keys;
  };
  function getValue(object, path) {
    return parts(path).reduce((value, key) => value == null ? undefined : value[key], object);
  }
  function setValue(object, path, value) {
    const keys = parts(path); let cursor = object;
    keys.slice(0, -1).forEach(key => {
      if (cursor[key] == null) cursor[key] = {};
      if (typeof cursor[key] !== 'object') throw new Error('字段结构不匹配');
      cursor = cursor[key];
    });
    cursor[keys[keys.length - 1]] = value;
  }
  function validURL(value) {
    if (!value || /^\{\{[A-Z][A-Z0-9_]*\}\}$/.test(value)) return true;
    try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password; } catch (_) { return false; }
  }
  function formatValue(value, format) {
    if (value == null) return format === 'jpy' ? '要確認' : '';
    if (format === 'jpy') return '¥' + Number(value).toLocaleString('ja-JP');
    if (format === 'strip-switchbot') return String(value).replace(/^SwitchBot\s+/, '');
    return String(value);
  }
  function editValue(data, path, value, type) {
    if (type === 'url' && !validURL(value)) throw new Error('链接须为 HTTPS，或保留 {{待替换变量}}');
    if (type === 'price') {
      if (value === '') value = null;
      else if (!/^\d+$/.test(String(value)) || !Number.isSafeInteger(Number(value))) throw new Error('价格请填写非负整数日元');
      else value = Number(value);
    }
    setValue(data, path, value);
    const offer = path.match(/^products\.(\d+)\.offer\./);
    if (offer) data.products[Number(offer[1])].offer.status = 'DRAFT';
    const sensitive = path.match(/^(coupon|brand|discovery|line)\./);
    if (sensitive) data[sensitive[1]].status = 'DRAFT';
    if (path === 'line.url' && data.line.qr_target && data.line.qr_target !== value) {
      data.line.qr_status = 'STALE_REGENERATE_REQUIRED';
    }
    return data;
  }
  function validatePrices(data) {
    (data.products || []).forEach(product => {
      const offer = product.offer || {}, sale = offer.sale_price_jpy, reference = offer.reference_price_jpy;
      if (Number.isInteger(sale) && Number.isInteger(reference) && reference < sale) throw new Error(product.name + '：比较价不能低于活动价');
    });
  }
  function exportData(data, changed) {
    validatePrices(data);
    const result = clone(data);
    if (result.line?.qr_target && result.line.qr_target !== result.line.url) {
      delete result.line.qr_image;
      delete result.line.qr_image_url;
      result.line.qr_status = 'STALE_REGENERATE_REQUIRED';
      result.line.status = 'DRAFT';
    }
    result._editor = {
      schema_version: '1.0', state: 'INTERNAL_DRAFT', qa_status: changed.length ? 'REVIEW_REQUIRED' : 'NOT_RETESTED',
      saved_at: new Date().toISOString(), changed_fields: [...new Set(changed)],
      render_note: '请使用 render_edm.py 重新生成 PNG；本编辑器不执行浏览器或邮件客户端 QA。'
    };
    return result;
  }
  function importData(original, imported, fields) {
    if (!imported || typeof imported !== 'object' || Array.isArray(imported)) throw new Error('文件不是 EDM 配置对象');
    if (JSON.stringify((imported.products || []).map(p => p.id)) !== JSON.stringify((original.products || []).map(p => p.id))) throw new Error('产品 ID 或顺序不匹配，请导入本稿导出的 JSON');
    const result = clone(original), changed = [];
    fields.forEach(field => {
      const value = getValue(imported, field.path);
      if (value !== undefined && JSON.stringify(value) !== JSON.stringify(getValue(original, field.path))) {
        if (!['string', 'number'].includes(typeof value) && value !== null) throw new Error('字段值必须是文字或数字');
        editValue(result, field.path, value == null ? '' : value, field.type); changed.push(field.path);
      }
    });
    for (const [key, enabled] of Object.entries(imported.module_enabled || {})) {
      if (!OPTIONAL_MODULES.has(key) && enabled === false) throw new Error('活动、商品、购买入口及页脚不能隐藏');
      if (OPTIONAL_MODULES.has(key)) { result.module_enabled ||= {}; result.module_enabled[key] = enabled !== false; }
    }
    if (imported.subject_options) {
      if (!Array.isArray(imported.subject_options) || imported.subject_options.length !== (original.subject_options || []).length) throw new Error('标题方案数量不匹配');
      result.subject_options = original.subject_options.map((option, i) => {
        const item = imported.subject_options[i];
        if (!item || item.id !== option.id || typeof item.subject !== 'string' || typeof item.preheader !== 'string') throw new Error('标题方案结构不匹配');
        return {...option, subject: item.subject, preheader: item.preheader};
      });
    }
    if (result.subject_options?.some(option => option.id === imported.selected_subject_option)) result.selected_subject_option = imported.selected_subject_option;
    return {data: result, changed: [...new Set(changed.concat(imported._editor?.changed_fields || []))]};
  }
  function applyDocument(doc, data, native = false) {
    if (native) validatePrices(data);
    doc.querySelectorAll('[data-edit]').forEach(node => {
      const path = node.getAttribute('data-edit'), value = getValue(data, path);
      if (path.startsWith('coupon.') && (value == null || value === '')) return;
      if (value !== undefined) {
        node.textContent = formatValue(value, node.getAttribute('data-edit-format') || node.getAttribute('data-format'));
        if (typeof value === 'string' && value.includes('\n')) node.style.whiteSpace = 'pre-line';
      }
    });
    doc.querySelectorAll('[data-edit-href]').forEach(node => {
      const value = getValue(data, node.getAttribute('data-edit-href'));
      if (value !== undefined && validURL(value)) {
        if (value) node.setAttribute('href', value); else node.removeAttribute('href');
      }
    });
    doc.querySelectorAll('[data-qr-target]').forEach(node => {
      if (node.getAttribute('data-qr-target') !== data.line?.url) {
        const section = node.closest('[data-module="line"]');
        const parent = node.parentElement;
        node.remove();
        if (parent?.tagName === 'A' && !parent.textContent.trim() && !parent.querySelector('img')) parent.remove();
        if (section && !section.querySelector('[data-stale-qr-note]')) {
          const note = doc.createElement('p');
          note.setAttribute('data-stale-qr-note', 'true');
          note.textContent = 'QRコードは更新確認中です。';
          note.style.cssText = 'font-size:11px;color:#946214;text-align:center;';
          (section.querySelector('td') || section).appendChild(note);
        }
      }
    });
    doc.querySelectorAll('[data-module]').forEach(node => {
      const module = node.getAttribute('data-module');
      if (OPTIONAL_MODULES.has(module) && data.module_enabled?.[module] === false) node.remove();
    });
    doc.querySelectorAll('[data-offer-product]').forEach(node => {
      const product = data.products?.find(p => p.id === node.getAttribute('data-offer-product'));
      if (!product) return;
      const index = data.products.indexOf(product), offer = product.offer || {};
      let referenceNode = node.querySelector('.reference-price');
      const reference = offer.reference_price_jpy, sale = offer.sale_price_jpy;
      if (Number.isInteger(reference) && (sale == null || reference >= sale)) {
        if (!referenceNode) {
          referenceNode = doc.createElement('del');
          referenceNode.className = 'reference-price';
          referenceNode.setAttribute('data-edit', 'products.' + index + '.offer.reference_price_jpy');
          referenceNode.setAttribute('data-edit-format', 'jpy');
          referenceNode.style.cssText = 'font-size:12px;color:#92949a;display:block;';
          node.appendChild(referenceNode);
        }
        referenceNode.textContent = formatValue(reference, 'jpy');
      } else if (referenceNode) referenceNode.remove();
      node.setAttribute('data-price-status', product.offer?.status || 'UNKNOWN');
      if (product.offer?.status === 'DRAFT' && !node.querySelector('[data-editor-price-note]')) {
        const note = doc.createElement('small'); note.setAttribute('data-editor-price-note', 'true');
        note.textContent = ' 参考価格・要確認'; note.style.cssText = 'font-size:10px;color:#946214;display:block;'; node.appendChild(note);
      }
    });
    doc.querySelectorAll('[data-discount-product]').forEach(node => {
      const product = data.products?.find(p => p.id === node.getAttribute('data-discount-product'));
      const offer = product?.offer || {}, sale = offer.sale_price_jpy, reference = offer.reference_price_jpy;
      if (Number.isInteger(sale) && Number.isInteger(reference) && reference > sale && sale >= 0) {
        node.textContent = Math.floor((reference - sale) / reference * 100) + '%OFF';
      } else { node.remove(); }
    });
    for (const module of ['coupon', 'discovery', 'brand', 'line']) {
      if (data[module]?.status === 'DRAFT') doc.querySelectorAll('[data-module="' + module + '"]').forEach(node => {
        if (!node.querySelector('[data-editor-review-note]')) {
          const note = doc.createElement('p'); note.setAttribute('data-editor-review-note', 'true');
          note.textContent = '内容は社内確認中です。'; note.style.cssText = 'font-size:11px;color:#946214;text-align:center;';
          (node.querySelector('td') || node).appendChild(note);
        }
      });
    }
    if (data.subject) doc.title = data.subject;
    const previewMeta = doc.querySelector('meta[name="edm-preheader"]');
    if (previewMeta) previewMeta.setAttribute('content', data.preheader || '');
    const preheader = doc.querySelector('[data-edit="preheader"]');
    if (preheader) preheader.textContent = data.preheader || '';
    doc.body.setAttribute('data-status', 'INTERNAL_DRAFT');
    if (native) {
      doc.querySelectorAll('script,iframe,object,embed,base,form,link[rel="stylesheet"]').forEach(node => node.remove());
      doc.querySelectorAll('*').forEach(node => {
        for (const attribute of Array.from(node.attributes)) {
          if (/^on/i.test(attribute.name) || attribute.name === 'contenteditable' || attribute.name.startsWith('data-edit')) node.removeAttribute(attribute.name);
        }
        if (node.hasAttribute('href') && !validURL(node.getAttribute('href'))) node.removeAttribute('href');
      });
      if (/data:[^;]+;base64,/i.test(doc.documentElement.outerHTML)) throw new Error('原生邮件中发现内嵌素材；请通过渲染器重新导出');
    }
    return '<!doctype html>\n' + doc.documentElement.outerHTML;
  }
  const api = {getValue, setValue, validURL, editValue, exportData, importData, formatValue, applyDocument};
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
  window.EDMEditorCore = api;

  const payload = JSON.parse(document.getElementById('edm-editor-payload').textContent);
  const decode = text => new TextDecoder().decode(Uint8Array.from(atob(text), c => c.charCodeAt(0)));
  const parser = new DOMParser();
  const original = clone(payload.original_data || payload.data);
  let data = clone(payload.data), changed = [...(payload.changed_fields || [])];
  const nativeBase = decode(payload.native_b64), previewBase = decode(payload.preview_b64);
  const originalDocument = parser.parseFromString(previewBase, 'text/html');
  const nativeDocument = parser.parseFromString(nativeBase, 'text/html');
  const frame = document.getElementById('email-preview');
  const moduleNames = {campaign_hero:'活动首屏',scenario_hero:'场景首屏',product_hero:'新品首屏',product_catalog:'大促商品列表',featured_product:'第一主推产品',featured_products:'重点产品',secondary_products:'精选产品',discovery:'新品／即将登场',coupon:'专属优惠码',brand:'品牌介绍',line:'LINE 入口',closing_cta:'再次购买入口',legal_footer:'条件与退订'};
  const labels = {subject:'邮件标题',preheader:'副标题／预览文字',campaign_name:'活动名称',hero_title:'主视觉标题',hero_support:'主视觉副文案',hero_kicker:'首屏引导',hero_footnote:'首屏补充说明',period_text:'活动期间',main_cta:'主按钮文字',main_url:'主购买入口',catalog_heading:'商品区域标题',featured_heading:'主推区域标题',secondary_heading:'精选区域标题',closing_heading:'结束标题',name:'商品名称',benefit:'一个主要利益点',label:'商品标签',note:'补充条件',url:'链接',cta:'按钮文字',sale_price_jpy:'活动价（日元）',reference_price_jpy:'比较价（日元）',title:'标题',body:'正文',code:'优惠码',benefit_text:'优惠利益',terms:'适用条件',valid_from:'开始时间',valid_until:'结束时间',preferences_url:'订阅设置链接',unsubscribe_url:'退订链接'};
  const found = new Map();
  for (const doc of [originalDocument, nativeDocument]) {
    doc.querySelectorAll('[data-edit],[data-edit-href]').forEach(node => {
      for (const attribute of ['data-edit', 'data-edit-href']) {
        const path = node.getAttribute(attribute); if (!path || found.has(path)) continue;
        const value = getValue(data, path); if (value !== undefined && value !== null && !['string','number'].includes(typeof value)) continue;
        found.set(path, {path, type: attribute === 'data-edit-href' ? 'url' : /_price_jpy$/.test(path) ? 'price' : 'text'});
      }
    });
  }
  for (const path of ['subject', 'preheader']) found.set(path, {path, type:'text'});
  (data.products || []).forEach((product, index) => {
    for (const key of ['sale_price_jpy', 'reference_price_jpy']) {
      const path = 'products.' + index + '.offer.' + key;
      found.set(path, {path, type:'price'});
    }
  });
  for (const key of ['valid_from','valid_until']) {
    if (data.coupon && Object.prototype.hasOwnProperty.call(data.coupon, key)) found.set('coupon.' + key, {path:'coupon.' + key, type:'text'});
  }
  const fields = [...found.values()];
  const modules = [...new Set([...originalDocument.querySelectorAll('[data-module]')].map(node => node.getAttribute('data-module')))];
  const tell = (message, error = false) => {const toast = document.getElementById('toast'); toast.textContent = message; toast.classList.toggle('error',error); toast.hidden = false; clearTimeout(window.edmToast); window.edmToast = setTimeout(() => toast.hidden = true, 5000);};
  const el = (tag, klass, text) => {const node = document.createElement(tag); if (klass) node.className = klass; if (text !== undefined) node.textContent = text; return node;};
  function mark(path) {if (!changed.includes(path)) changed.push(path); document.getElementById('change-count').textContent = changed.length ? changed.length + ' 项修改 · 待复核' : '内部稿 · 待确认';}
  function setField(path, value, type) {
    editValue(data, path, value, type); mark(path);
    const option = data.subject_options?.find(item => item.id === data.selected_subject_option);
    if (option && (path === 'subject' || path === 'preheader')) option[path] = value;
    document.querySelectorAll('[data-control-path]').forEach(node => {if (node.dataset.controlPath === path && node !== document.activeElement) node.value = value ?? '';});
    renderSubjects();
  }
  function makeField(field) {
    const wrap = el('label','field'); wrap.appendChild(el('span','field-label',labels[field.path.split('.').pop()] || field.path));
    const input = el(field.type === 'text' ? 'textarea' : 'input');
    if (field.type === 'text') input.rows = /benefit|body|terms|preheader|note/.test(field.path) ? 3 : 2;
    else {input.type = 'text'; if (field.type === 'price') input.inputMode = 'numeric';}
    input.value = getValue(data, field.path) ?? ''; input.dataset.controlPath = field.path;
    input.addEventListener('input', () => {try {setField(field.path, input.value, field.type); input.removeAttribute('aria-invalid'); schedulePreview();} catch (error) {input.setAttribute('aria-invalid','true'); tell(error.message,true);}});
    wrap.appendChild(input); return wrap;
  }
  function sourceLine(url, label) {
    const p = el('p','source-line');
    if (url && validURL(url) && /^https:/.test(url)) {const a = el('a','',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';p.appendChild(a);}
    else p.textContent = label + '：待补';
    return p;
  }
  function renderFields() {
    const panel = document.getElementById('fields'); panel.replaceChildren();
    const general = el('details','field-group');general.open=true;general.appendChild(el('summary','','活动与入口'));
    fields.filter(field => !field.path.startsWith('products.') && !/^(coupon|brand|discovery|line)\./.test(field.path)).forEach(field => general.appendChild(makeField(field)));
    panel.appendChild(general);
    (data.products || []).forEach((product,index) => {
      const group=el('details','field-group');group.appendChild(el('summary','',String(index+1).padStart(2,'0')+' · '+product.name.replace(/^SwitchBot\s+/,'')));
      const status=el('p','field-note',(product.offer?.status === 'CONFIRMED' ? '来源状态：已确认' : '来源状态：参考价／待确认')+'；修改后需复核。');group.appendChild(status);
      fields.filter(field => field.path.startsWith('products.'+index+'.')).forEach(field => group.appendChild(makeField(field)));
      group.appendChild(sourceLine(product.offer?.source,'查看价格来源'));group.appendChild(sourceLine(product.product_source,'查看产品来源'));panel.appendChild(group);
    });
    for (const name of ['discovery','coupon','brand','line']) {
      const matched=fields.filter(field => field.path.startsWith(name+'.'));if (!matched.length) continue;
      const group=el('details','field-group');group.appendChild(el('summary','',moduleNames[name]));
      matched.forEach(field => group.appendChild(makeField(field)));group.appendChild(sourceLine(data[name]?.source,'查看模块来源'));panel.appendChild(group);
    }
  }
  function renderSubjects() {
    const container=document.getElementById('subject-options');container.replaceChildren();
    const options=data.subject_options || [{id:'current',label:'当前方案',subject:data.subject,preheader:data.preheader}];
    options.forEach((option,index) => {
      const selected=option.id === data.selected_subject_option || (!data.selected_subject_option && option.subject === data.subject);
      const card=el('button','subject-card'+(selected?' selected':''));card.type='button';card.setAttribute('aria-pressed',String(selected));
      card.appendChild(el('span','option-number',String(index+1).padStart(2,'0')+' · '+(option.label || '标题方向')));
      card.appendChild(el('strong','',option.subject));card.appendChild(el('span','option-preview',option.preheader));
      card.addEventListener('click',()=>{data.selected_subject_option=option.id;data.subject=option.subject;data.preheader=option.preheader;mark('subject');mark('preheader');renderSubjects();renderFields();updatePreview();});
      container.appendChild(card);
    });
    document.getElementById('selected-subject').textContent=data.subject;
    document.getElementById('selected-preheader').textContent=data.preheader;
  }
  function renderModules() {
    const list=document.getElementById('modules');list.replaceChildren();
    modules.forEach(name=>{const label=el('label','module-toggle');const input=el('input');input.type='checkbox';input.checked=data.module_enabled?.[name] !== false;input.disabled=!OPTIONAL_MODULES.has(name);
      input.addEventListener('change',()=>{data.module_enabled ||= {};data.module_enabled[name]=input.checked;mark('module_enabled.'+name);updatePreview();});
      label.append(input,el('span','',moduleNames[name] || name));if(input.disabled)label.appendChild(el('small','','固定'));list.appendChild(label);});
  }
  function markup(native) {return applyDocument(parser.parseFromString(native?nativeBase:previewBase,'text/html'),data,native);}
  let timer;
  function schedulePreview(){clearTimeout(timer);timer=setTimeout(updatePreview,200);}
  function updatePreview(){
    const doc=parser.parseFromString(markup(false),'text/html');
    const csp=doc.createElement('meta');csp.httpEquiv='Content-Security-Policy';csp.content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:;";doc.head.prepend(csp);
    const editStyle=doc.createElement('style');editStyle.textContent='[contenteditable="true"]:hover{outline:1px dashed #ef672d;outline-offset:4px;}[contenteditable="true"]:focus{outline:2px solid #ef672d;outline-offset:4px;}';doc.head.appendChild(editStyle);
    frame.srcdoc='<!doctype html>'+doc.documentElement.outerHTML;
    document.getElementById('selected-subject').textContent=data.subject;document.getElementById('selected-preheader').textContent=data.preheader;
  }
  frame.addEventListener('load',()=>{
    const doc=frame.contentDocument;if(!doc)return;
    doc.addEventListener('click',event=>{if(event.target.closest('a'))event.preventDefault();});
    if(document.getElementById('inline-edit').checked)doc.querySelectorAll('[data-edit]').forEach(node=>{
      const path=node.getAttribute('data-edit'),field=found.get(path);if(!field || field.type !== 'text' || node.tagName === 'TITLE' || path === 'preheader')return;
      node.contentEditable='true';node.addEventListener('input',()=>{try{let value=node.innerText ?? node.textContent;if(node.getAttribute('data-edit-format') === 'strip-switchbot')value='SwitchBot '+value.replace(/^SwitchBot\s+/,'');setField(path,value,'text');}catch(error){tell(error.message,true);}});
      node.addEventListener('blur',schedulePreview);
    });
    const resize=()=>{frame.style.height=Math.max(800,doc.documentElement.scrollHeight,doc.body.scrollHeight)+'px';};resize();
    doc.querySelectorAll('img').forEach(img=>img.addEventListener('load',resize));if(doc.fonts?.ready)doc.fonts.ready.then(resize);
  });
  function download(name, text, type){const url=URL.createObjectURL(new Blob([text],{type}));const a=el('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  document.getElementById('save-json').addEventListener('click',()=>{try{download('render-input-edited.json',JSON.stringify(exportData(data,changed),null,2),'application/json');tell('已导出配置；保留原素材目录即可重新渲染。');}catch(error){tell(error.message,true);}});
  document.getElementById('save-email').addEventListener('click',()=>{try{download('email-edited-internal.html',markup(true),'text/html');tell('已导出内部邮件 HTML；发送前须复核修改、图片 URL 和优惠条件。');}catch(error){tell(error.message,true);}});
  document.getElementById('save-review').addEventListener('click',()=>{
    try {
    const doc=document.documentElement.cloneNode(true);doc.querySelector('#edm-editor-payload').textContent=JSON.stringify({...payload,original_data:original,data:exportData(data,changed),changed_fields:changed}).replace(/</g,'\\u003c');
    const outputFrame=doc.querySelector('#email-preview');outputFrame.removeAttribute('srcdoc');outputFrame.removeAttribute('style');doc.querySelector('#toast').hidden=true;
    download('editable-review-updated.html','<!doctype html>\n'+doc.outerHTML,'text/html');tell('已保存可继续编辑的 HTML，包含本次修改与素材。');
    } catch(error) {tell(error.message,true);}
  });
  document.getElementById('load-json').addEventListener('click',()=>document.getElementById('json-file').click());
  document.getElementById('json-file').addEventListener('change',async event=>{try{
    const file=event.target.files[0];if(!file)return;if(file.size>10000000)throw new Error('配置文件过大');
    const imported=JSON.parse(await file.text());const result=importData(original,imported,fields);data=result.data;changed=result.changed;renderFields();renderSubjects();renderModules();updatePreview();mark('_import');tell('已导入；历史来源和官方素材保持原绑定。');
  }catch(error){tell(error.message,true);}event.target.value='';});
  document.getElementById('inline-edit').addEventListener('change',updatePreview);
  document.querySelectorAll('[data-width]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-width]').forEach(other=>other.classList.toggle('active',other===button));document.getElementById('preview-shell').style.width=button.dataset.width+'px';updatePreview();}));
  document.getElementById('reset').addEventListener('click',()=>{if(!window.confirm('恢复最初稿件？当前未保存修改将丢失。'))return;data=clone(original);changed=[];renderFields();renderSubjects();renderModules();updatePreview();document.getElementById('change-count').textContent='内部稿 · 待确认';});
  document.getElementById('copy-subject').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(data.subject+'\n'+data.preheader);tell('已复制选中的标题与副标题。');}catch(_){tell('浏览器未允许剪贴板，请从左侧字段复制。',true);}});
  document.getElementById('product-count').textContent=(data.products || []).length+' 个产品';
  renderFields();renderSubjects();renderModules();updatePreview();
})();
'''


SHELL = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EDM 可编辑审阅</title>
<style>
:root{--ink:#20313d;--muted:#77848d;--line:#dce3e4;--paper:#f4f6f5;--accent:#e35f30;--green:#26655a}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif}button,input,textarea{font:inherit}button{cursor:pointer}button:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid #e6a388;outline-offset:3px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:19px 28px;background:#fff;border-bottom:1px solid var(--line)}.brand-label{font-weight:800;font-size:19px;letter-spacing:-.5px}.brand-label small{font-size:11px;font-weight:500;letter-spacing:1.6px;color:var(--muted);display:block}.top-actions{display:flex;flex-wrap:wrap;gap:8px}.btn{border:1px solid #cbd5d7;background:#fff;color:var(--ink);border-radius:8px;padding:9px 13px;font-size:12px;font-weight:600}.btn.primary{background:var(--ink);color:white;border-color:var(--ink)}.btn:hover{border-color:var(--accent)}.status-bar{padding:10px 28px;display:flex;gap:20px;align-items:center;font-size:11px;background:#fef8ed;color:#786446;border-bottom:1px solid #efe4d0}.status-dot{width:6px;height:6px;background:#da943f;display:inline-block;border-radius:100%;margin-right:7px}.workspace{display:grid;grid-template-columns:310px minmax(0,1fr);min-height:100vh}.sidebar{background:white;border-right:1px solid var(--line);padding:22px 18px}.side-title{font-size:12px;font-weight:800;letter-spacing:1px;margin-bottom:12px}.side-note{font-size:11px;color:var(--muted);line-height:1.8;margin:0 0 18px}.field-group{border:1px solid var(--line);border-radius:10px;margin:10px 0;background:white;overflow:hidden}.field-group summary{padding:12px;cursor:pointer;font-size:12px;font-weight:700;background:#fafbfa}.field-group[open] summary{border-bottom:1px solid var(--line);margin-bottom:8px}.field{display:block;padding:6px 11px 9px}.field-label{font-size:11px;color:#6e7b84;display:block;margin-bottom:4px}.field textarea,.field input{width:100%;min-width:0;border:1px solid #dce2e3;border-radius:6px;background:#fff;padding:8px;color:var(--ink);font-size:12px;line-height:1.6;resize:vertical}.field [aria-invalid="true"]{border-color:#d14135;background:#fff3ef}.field-note,.source-line{font-size:10px;line-height:1.7;margin:8px 12px;color:#88764f}.source-line a{color:var(--green);text-decoration:underline}.module-toggle{display:flex;gap:9px;align-items:center;font-size:12px;margin:10px 0}.module-toggle input{accent-color:var(--green);width:15px;height:15px}.module-toggle small{margin-left:auto;font-size:10px;color:#9aa3a8}.modules-wrap{padding-top:22px;margin-top:20px;border-top:1px solid var(--line)}.content{padding:26px 30px 50px;min-width:0}.eyebrow{font-size:10px;letter-spacing:1.5px;color:#8b969b;font-weight:700}.content h1{font-size:25px;letter-spacing:-1px;margin:5px 0 5px}.intro{font-size:12px;color:var(--muted);margin:0 0 22px}.subject-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:17px 0 22px}.subject-card{padding:16px 17px;display:flex;flex-direction:column;gap:9px;text-align:left;border:1px solid #dce3e4;border-radius:11px;background:#fff;color:var(--ink);line-height:1.65;min-width:0}.subject-card.selected{border:2px solid var(--green);padding:15px 16px;background:#f1f7f3;box-shadow:0 3px 15px #184d2e06}.option-number{font-size:10px;letter-spacing:.3px;color:var(--green);font-weight:700}.subject-card strong{font-size:13px;font-weight:650}.option-preview{font-size:11px;color:#7d898d}.preview-toolbar{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;border:1px solid var(--line);border-radius:11px 11px 0 0;background:#fff;gap:12px}.width-switch{display:inline-flex;background:#f0f3f2;padding:3px;border-radius:7px;gap:4px}.width-switch button{border:0;background:transparent;padding:6px 11px;color:#7b898b;font-size:11px;border-radius:5px}.width-switch .active{background:white;color:var(--ink);box-shadow:0 1px 4px #20313d18}.inline-switch{font-size:11px;color:#6f7f83;display:flex;align-items:center;gap:6px}.inline-switch input{accent-color:var(--green)}.preview-area{background:#e9eeec;border:1px solid var(--line);border-top:0;padding:28px 16px;overflow:auto;border-radius:0 0 12px 12px}.preview-shell{width:600px;max-width:100%;margin:auto;box-shadow:0 6px 25px #14272312;background:white;border-radius:5px;overflow:hidden}.inbox-strip{background:white;padding:18px 19px;border-bottom:1px solid #e4e8e7;font-size:11px}.inbox-strip small{color:#98a19f;font-size:10px}.inbox-strip strong{display:block;font-size:12px;margin:5px 0;color:#334344}.inbox-strip p{margin:0;color:#87928e;font-size:11px}iframe{display:block;width:100%;height:800px;border:0;background:white}.preview-note{font-size:11px;color:#87928e;text-align:center;margin:14px 0 0}.note-box{font-size:11px;color:#647675;line-height:1.85;background:#edf3ef;border-radius:8px;padding:12px;margin-top:15px}.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);max-width:90%;background:#263e38;color:white;box-shadow:0 6px 20px #0002;border-radius:9px;padding:12px 20px;font-size:12px;z-index:10}.toast.error{background:#953e2c}.source-summary{display:flex;align-items:center;gap:10px;font-size:11px;color:#899694}.source-summary span{background:#eaf0ed;color:var(--green);padding:4px 8px;border-radius:5px}.header-row{display:flex;align-items:flex-end;justify-content:space-between;gap:12px}.reset{font-size:11px;color:#899491;border:0;background:none;margin-top:20px;padding:0;text-decoration:underline}@media(max-width:1080px){.workspace{grid-template-columns:280px minmax(0,1fr)}.content{padding:22px 18px}.subject-options{grid-template-columns:1fr}.subject-card{gap:5px}.topbar{padding:16px 18px}.status-bar{padding:9px 18px}}@media(max-width:720px){.topbar{align-items:flex-start;flex-direction:column;gap:12px}.workspace{display:flex;flex-direction:column}.sidebar{border-right:0;border-bottom:1px solid var(--line);max-height:460px;overflow:auto}.content{padding:20px 10px}.subject-options{gap:8px}.preview-toolbar{flex-wrap:wrap;padding:10px}.preview-area{padding:12px 4px}.status-bar{display:block}.source-summary{display:none}}@media print{.sidebar,.top-actions,.subject-options,.preview-toolbar,.preview-note,.status-bar{display:none}.workspace{display:block}.content{padding:0}.preview-area{padding:0;border:0}.preview-shell{box-shadow:none}}
</style></head><body>
<header class="topbar"><div class="brand-label">SwitchBot <span style="font-weight:400;color:#9da7aa">/</span> EDM Studio<small>秋促邮件 · 可编辑审阅</small></div><div class="top-actions"><button class="btn" id="load-json">导入修改</button><button class="btn" id="save-json">保存 JSON</button><button class="btn" id="save-email">导出邮件 HTML</button><button class="btn primary" id="save-review">保存可编辑 HTML</button></div></header>
<div class="status-bar"><span><i class="status-dot"></i><strong id="change-count">内部稿 · 待确认</strong></span><span>本页只在当前设备编辑；修改不会自动写回飞书，也不会发送邮件。</span></div>
<div class="workspace"><aside class="sidebar"><div class="side-title">编辑内容</div><p class="side-note">从左侧修改文案、价格和链接。也可以开启「直接编辑预览文字」。导出 HTML 可保留修改继续使用。</p><div id="fields"></div><div class="modules-wrap"><div class="side-title">模块开关</div><div id="modules"></div></div><div class="note-box">价格、优惠码和品牌内容的手动修改会保留为待复核。原始来源不会因编辑而变成“已确认”。</div><button class="reset" id="reset">恢复最初稿件</button></aside>
<main class="content"><div class="header-row"><div><div class="eyebrow">SUBJECT & PREHEADER</div><h1>先选一个打开理由。</h1></div><div class="source-summary"><span id="product-count"></span><span>600 / 390 px</span></div></div><p class="intro">标题负责吸引打开，副标题补充购买理由。点击选择后，可在左侧继续改写。</p><div class="subject-options" id="subject-options"></div>
<div class="preview-toolbar"><div class="width-switch"><button class="active" data-width="600">桌面 600</button><button data-width="390">手机 390</button></div><label class="inline-switch"><input type="checkbox" id="inline-edit">直接编辑预览文字</label><button class="btn" id="copy-subject">复制标题与副标题</button></div>
<div class="preview-area"><div class="preview-shell" id="preview-shell"><div class="inbox-strip"><small>SWITCHBOT株式会社 · 收件箱预览</small><strong id="selected-subject"></strong><p id="selected-preheader"></p></div><iframe id="email-preview" title="日语邮件内容预览" sandbox="allow-same-origin"></iframe></div></div><p class="preview-note">导出的 PNG 由邮件 HTML 排版渲染。修改后请保存 JSON 再重新渲染；此页不宣称已通过邮件客户端实测。</p></main></div>
<input type="file" id="json-file" accept="application/json,.json" hidden><div class="toast" id="toast" hidden role="status"></div>
<script id="edm-editor-payload" type="application/json">__PAYLOAD__</script><script>__JAVASCRIPT__</script></body></html>'''


def build_editor(data, preview_html, native_html, out_path):
    """Write the standalone editor; inputs must be renderer-produced HTML strings."""
    if not isinstance(data, dict) or not data.get("subject") or not data.get("preheader"):
        raise ValueError("Current subject and preheader are required")
    for value in (preview_html, native_html):
        if not isinstance(value, str) or "<html" not in value.lower():
            raise ValueError("Rendered preview and native HTML are required")
    options = data.get("subject_options", [])
    if options and (not isinstance(options, list) or len({item.get("id") for item in options}) != len(options)
                    or any(not all(isinstance(item.get(key), str) and item[key].strip() for key in ("id", "subject", "preheader")) for item in options)):
        raise ValueError("Subject options require unique ids, subject and preheader")
    payload = {
        "schema_version": "1.0", "data": data,
        "native_b64": base64.b64encode(native_html.encode("utf-8")).decode("ascii"),
        "preview_b64": base64.b64encode(preview_html.encode("utf-8")).decode("ascii"),
    }
    encoded = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    result = SHELL.replace("__JAVASCRIPT__", EDITOR_JS, 1).replace("__PAYLOAD__", encoded, 1)
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result, encoding="utf-8")
    return {"file": target.name, "status": "INTERNAL_DRAFT", "editable": True,
            "subject_options": len(options) or 1, "native_export": "SEPARATE_NATIVE_HTML_BASELINE",
            "storage": "LOCAL_DOWNLOAD_ONLY", "browser_qa": "NOT_EXECUTED", "png_export": "RENDERER_REQUIRED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--preview", required=True)
    parser.add_argument("--native", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = build_editor(json.loads(Path(args.input).read_text(encoding="utf-8")),
                          Path(args.preview).read_text(encoding="utf-8"),
                          Path(args.native).read_text(encoding="utf-8"), args.out)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
