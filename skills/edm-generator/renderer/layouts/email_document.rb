module PilotRenderer
  module EmailDocument
    module_function

    def render(title:, css:, body:, case_id:, gate:)
      <<~HTML
        <!doctype html>
        <html lang="ja">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
          <link rel="icon" href="data:,">
          <title>#{title}</title>
          <style>#{css}</style>
        </head>
        <body data-pilot="#{case_id}" data-gate="#{gate}">
          <main class="email-canvas">#{body}</main>
        </body>
        </html>
      HTML
    end
  end
end
