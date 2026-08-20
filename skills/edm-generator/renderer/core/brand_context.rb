require "yaml"

module PilotRenderer
  class BrandContext
    attr_reader :root, :rules

    def initialize(root:)
      @root = root
      @rules = YAML.load_file(File.join(root, "brand_system", "switchbot_composition_rules_v1.0.yaml"))
    end

    def render_mode(brand:, market:)
      switchbot_japan?(brand: brand, market: market) ? "switchbot_brand" : "generic"
    end

    def assert_switchbot_brand!(brand:, market:)
      mode = render_mode(brand: brand, market: market)
      raise "SwitchBot Japan must use switchbot_brand mode" unless mode == "switchbot_brand"
      raise "Brand layer is not additive" unless rules.dig("scope", "mutation_policy").to_s.include?("Additive")

      mode
    end

    private

    def switchbot_japan?(brand:, market:)
      brand.to_s.casecmp("SwitchBot").zero? && market.to_s.casecmp("Japan").zero?
    end
  end
end

