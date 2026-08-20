require "erb"

module PilotRenderer
  module EmailComponents
    module_function

    def esc(value)
      ERB::Util.html_escape(value.to_s)
    end

    def internal_notice(text)
      %(<div class="pilot-notice" role="note">#{esc(text)}</div>)
    end

    def brand_header(label)
      <<~HTML
        <header class="brand-header">
          <span class="brand-mark">SwitchBot</span>
          <span class="brand-context">#{esc(label)}</span>
        </header>
      HTML
    end

    def hero(product:, headline:, subheadline:, image:, alt:, tone: "light")
      <<~HTML
        <section class="hero hero--#{esc(tone)}" data-module="MOD-HERO-PRODUCT">
          <div class="hero__copy">
            <p class="product-name">#{esc(product)}</p>
            <h1>#{esc(headline)}</h1>
            <p class="hero__lede">#{esc(subheadline)}</p>
          </div>
          <figure class="hero__visual">
            <img src="#{esc(image)}" width="1200" height="1200" alt="#{esc(alt)}" fetchpriority="high">
          </figure>
        </section>
      HTML
    end

    def image_story(title:, body:, image:, alt:, module_id:, reverse: false, note: nil)
      cls = reverse ? "story story--reverse" : "story"
      note_html = note ? %(<p class="source-note">#{esc(note)}</p>) : ""
      <<~HTML
        <section class="#{cls}" data-module="#{esc(module_id)}">
          <div class="story__copy">
            <h2>#{esc(title)}</h2>
            <p>#{esc(body)}</p>
            #{note_html}
          </div>
          <figure class="story__visual">
            <img src="#{esc(image)}" width="1200" height="1200" alt="#{esc(alt)}" loading="lazy">
          </figure>
        </section>
      HTML
    end

    def full_visual(title:, body:, image:, alt:, module_id:, note: nil)
      note_html = note ? %(<p class="source-note">#{esc(note)}</p>) : ""
      <<~HTML
        <section class="full-visual" data-module="#{esc(module_id)}">
          <div class="full-visual__head">
            <h2>#{esc(title)}</h2>
            <p>#{esc(body)}</p>
          </div>
          <figure><img src="#{esc(image)}" width="1200" height="1200" alt="#{esc(alt)}" loading="lazy"></figure>
          #{note_html}
        </section>
      HTML
    end

    def fact_strip(items)
      rows = items.map { |item| %(<li><span>#{esc(item[:label])}</span><strong>#{esc(item[:value])}</strong></li>) }.join
      %(<section class="fact-strip" aria-label="Verified content summary"><ul>#{rows}</ul></section>)
    end

    def cta_band(title:, label:, url:)
      <<~HTML
        <section class="cta-band" data-module="MOD-CONV-CTA-BAND">
          <h2>#{esc(title)}</h2>
          <a href="#{esc(url)}" class="primary-cta">#{esc(label)}</a>
        </section>
      HTML
    end

    def brand_footer
      <<~HTML
        <footer class="brand-footer" data-module="MOD-SYSTEM-BRAND-FOOTER">
          <strong>SwitchBot</strong>
          <p>社内検証用レンダリング。配信・転送・外部公開はできません。</p>
          <p>正式配信には、現行の会社情報・配信管理・退会導線を含む承認済み Footer が必要です。</p>
        </footer>
      HTML
    end
  end
end

