module PilotRenderer
  module JapaneseTypography
    module_function

    def character_count(text)
      text.to_s.gsub(/\s+/, "").length
    end

    def source_safe(text)
      text.to_s.strip.gsub("...", "…").gsub("--", "—")
    end
  end
end

