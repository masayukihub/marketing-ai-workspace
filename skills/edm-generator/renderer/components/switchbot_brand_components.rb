require "erb"

module PilotRenderer
  module SwitchBotBrandComponents
    module_function

    def esc(value)
      ERB::Util.html_escape(value.to_s)
    end

    def internal_notice(text)
      %(<div class="sb-pilot-notice" role="note">#{esc(text)}</div>)
    end

    def brand_header(context:, chapter:)
      <<~HTML
        <header class="sb-brand-header">
          <strong class="sb-wordmark">SwitchBot</strong>
          <span>#{esc(context)}</span>
          <small>#{esc(chapter)}</small>
        </header>
      HTML
    end

    def hero(product:, headline:, body:, image:, alt:, module_id:, theme:)
      <<~HTML
        <section class="sb-hero sb-tone--#{esc(theme)}" data-module="#{esc(module_id)}">
          <div class="sb-hero__copy">
            <p class="sb-eyebrow">#{esc(product)}</p>
            <h1>#{esc(headline)}</h1>
            <p class="sb-lede">#{esc(body)}</p>
          </div>
          <figure class="sb-hero__visual"><img src="#{esc(image)}" width="1200" height="1200" alt="#{esc(alt)}" fetchpriority="high"></figure>
        </section>
      HTML
    end

    def statement(kicker:, title:, body:, module_id:, tone: "paper")
      <<~HTML
        <section class="sb-statement sb-tone--#{esc(tone)}" data-module="#{esc(module_id)}">
          <p class="sb-kicker">#{esc(kicker)}</p>
          <h2>#{esc(title)}</h2>
          <p>#{esc(body)}</p>
        </section>
      HTML
    end

    def visual_feature(kicker:, title:, body:, image:, alt:, module_id:, note:, tone: "paper", media_class: nil)
      note_html = note.to_s.empty? ? "" : %(<p class="sb-source-note">#{esc(note)}</p>)
      figure_class = media_class.to_s.empty? ? "" : %( class="#{esc(media_class)}")
      <<~HTML
        <section class="sb-visual-feature sb-tone--#{esc(tone)}" data-module="#{esc(module_id)}">
          <div class="sb-section-copy">
            <p class="sb-kicker">#{esc(kicker)}</p>
            <h2>#{esc(title)}</h2>
            <p>#{esc(body)}</p>
          </div>
          <figure#{figure_class}><img src="#{esc(image)}" width="1200" height="1200" alt="#{esc(alt)}" loading="lazy"></figure>
          #{note_html}
        </section>
      HTML
    end

    def split_feature(kicker:, title:, body:, image:, alt:, module_id:, note:, reverse: false, tone: "white")
      reverse_class = reverse ? " sb-split-feature--reverse" : ""
      note_html = note.to_s.empty? ? "" : %(<p class="sb-source-note">#{esc(note)}</p>)
      <<~HTML
        <section class="sb-split-feature#{reverse_class} sb-tone--#{esc(tone)}" data-module="#{esc(module_id)}">
          <div class="sb-split-feature__copy">
            <p class="sb-kicker">#{esc(kicker)}</p>
            <h2>#{esc(title)}</h2>
            <p>#{esc(body)}</p>
            #{note_html}
          </div>
          <figure><img src="#{esc(image)}" width="1200" height="1200" alt="#{esc(alt)}" loading="lazy"></figure>
        </section>
      HTML
    end

    def checklist(kicker:, title:, items:, module_id:, note:)
      rows = items.map.with_index(1) do |item, index|
        %(<li><span>#{format("%02d", index)}</span><strong>#{esc(item)}</strong></li>)
      end.join
      note_html = note.to_s.empty? ? "" : %(<p class="sb-source-note">#{esc(note)}</p>)
      <<~HTML
        <section class="sb-checklist" data-module="#{esc(module_id)}">
          <p class="sb-kicker">#{esc(kicker)}</p>
          <h2>#{esc(title)}</h2>
          <ol>#{rows}</ol>
          #{note_html}
        </section>
      HTML
    end

    def cta_checkpoint(title:, body:, label:, url:, module_id:)
      <<~HTML
        <section class="sb-cta-checkpoint" data-module="#{esc(module_id)}">
          <div><p class="sb-kicker">CHECKPOINT</p><h2>#{esc(title)}</h2><p>#{esc(body)}</p></div>
          <a class="sb-cta sb-cta--outline" href="#{esc(url)}">#{esc(label)}</a>
        </section>
      HTML
    end

    def product_reset(product:, title:, image:, alt:, module_id:, note:)
      note_html = note.to_s.empty? ? "" : %(<p class="sb-source-note">#{esc(note)}</p>)
      <<~HTML
        <section class="sb-product-reset" data-module="#{esc(module_id)}">
          <figure><img src="#{esc(image)}" width="1200" height="1200" alt="#{esc(alt)}" loading="lazy"></figure>
          <div><p class="sb-eyebrow">#{esc(product)}</p><h2>#{esc(title)}</h2>#{note_html}</div>
        </section>
      HTML
    end

    def final_cta(title:, body:, label:, url:, module_id:)
      <<~HTML
        <section class="sb-final-cta" data-module="#{esc(module_id)}">
          <p class="sb-kicker">NEXT STEP</p>
          <h2>#{esc(title)}</h2>
          <p>#{esc(body)}</p>
          <a class="sb-cta" href="#{esc(url)}">#{esc(label)}</a>
        </section>
      HTML
    end

    def brand_footer(case_id:, module_id: "MOD-SYSTEM-BRAND-FOOTER")
      <<~HTML
        <footer class="sb-brand-footer" data-module="#{esc(module_id)}">
          <div class="sb-brand-footer__mark"><strong>SwitchBot</strong><span>Japan EDM · Brand Calibration</span></div>
          <div class="sb-brand-footer__grid">
            <div><small>DELIVERY STATUS</small><p>社内検証用 · 配信不可</p></div>
            <div><small>PRODUCTION FOOTER</small><p>承認済み会社情報・配信管理・退会導線が必要</p></div>
            <div><small>CASE</small><p>#{esc(case_id)} / Brand V2</p></div>
          </div>
          <p class="sb-brand-footer__note">現在の Footer はブランドの「深い終了リズム」を検証する構造サンプルです。正式な法務・サービス・配信リンクを代替しません。</p>
        </footer>
      HTML
    end

    def production_footer(footer:, case_id:, production_status:, module_id: "MOD-SYSTEM-BRAND-FOOTER")
      legal_links = footer.fetch("required_legal").map do |item|
        %(<a href="#{esc(item.fetch("url"))}">#{esc(item.fetch("label"))}</a>)
      end.join(%(<span aria-hidden="true"> · </span>))
      preference = footer.fetch("preference_center")
      unsubscribe = footer.fetch("unsubscribe")
      <<~HTML
        <footer class="sb-brand-footer sb-production-footer" data-module="#{esc(module_id)}" data-footer-component="#{esc(footer.fetch("component_id"))}">
          <div class="sb-brand-footer__mark">
            <strong>#{esc(footer.dig("brand", "value"))}</strong>
            <span>暮らしに、心地よいテクノロジーを。</span>
          </div>
          <div class="sb-production-footer__links">
            <a href="#{esc(footer.dig("official_store", "value"))}">SwitchBot公式サイト</a>
            #{legal_links}
          </div>
          <p class="sb-production-footer__runtime">
            <a data-runtime-token="preference_center_url" href="#{esc(preference.dig("url", "value"))}">#{esc(preference.dig("label", "value"))}</a>
            <span aria-hidden="true"> / </span>
            <a data-runtime-token="unsubscribe_url" href="#{esc(unsubscribe.dig("url", "value"))}">#{esc(unsubscribe.dig("label", "value"))}</a>
          </p>
          <div class="sb-brand-footer__grid sb-brand-footer__grid--two">
            <div><small>発行元</small><p>#{esc(footer.dig("company", "value"))}<br>#{esc(footer.dig("address", "value"))}</p></div>
            <div><small>カスタマーサポート</small><p>#{esc(footer.dig("support_email", "value"))}<br>#{esc(footer.dig("support_phone", "value"))}</p></div>
          </div>
          <p class="sb-brand-footer__note">#{esc(footer.dig("copyright", "value").gsub("{{current_year}}", Time.now.year.to_s))}</p>
        </footer>
      HTML
    end
  end
end
