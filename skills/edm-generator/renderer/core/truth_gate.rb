require "yaml"

module PilotRenderer
  class TruthGate
    REQUIRED_PACKS = %w[product_truth campaign_truth asset_manifest copy_verification_input].freeze

    attr_reader :pilot_id, :root, :packs

    def initialize(root:, pilot_id:)
      @root = root
      @pilot_id = pilot_id
      @packs = REQUIRED_PACKS.to_h do |name|
        path = File.join(root, "pilot", pilot_id, "truth_pack", "#{name}.yaml")
        raise "Missing truth pack: #{path}" unless File.file?(path)
        [name, YAML.load_file(path)]
      end
    end

    def status
      packs.fetch("campaign_truth").fetch("verification_status")
    end

    def renderable?
      %w[READY CONDITIONAL].include?(status)
    end

    def assert_renderable!
      raise "#{pilot_id} is #{status}; final renderer is not allowed" unless renderable?

      cta = packs.fetch("campaign_truth").fetch("cta_url")
      raise "#{pilot_id} has no verified CTA" unless cta["status"] == "VERIFIED" && cta["value"].to_s.start_with?("https://")

      assets = packs.fetch("asset_manifest").fetch("assets")
      has_main = assets.any? do |asset|
        asset["asset_type"] == "official_png" && asset["status"] == "VERIFIED" && asset["approved"] == true
      end
      raise "#{pilot_id} has no verified official main asset" unless has_main
      true
    end
  end
end

