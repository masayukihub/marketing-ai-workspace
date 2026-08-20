# frozen_string_literal: true

require "yaml"
require "pathname"
require "uri"
require "date"
require "time"

module ProductionEDM
  module Support
    module_function

    ALLOWED_STATES = %w[VERIFIED APPROVED UNVERIFIED MISSING NOT_REQUIRED].freeze

    def load_yaml(root, relative)
      YAML.safe_load(File.read(File.join(root, relative)), permitted_classes: [Date, Time, Symbol], aliases: true)
    end

    def value(node)
      node.is_a?(Hash) && node.key?("value") ? node["value"] : node
    end

    def status(node)
      node.is_a?(Hash) ? node["status"] : nil
    end

    def valid_http_url?(value)
      uri = URI.parse(value.to_s)
      %w[http https].include?(uri.scheme) && !uri.host.to_s.empty?
    rescue URI::InvalidURIError
      false
    end

    def relative_asset(root, output_dir, source_path)
      absolute = Pathname.new(File.join(root, source_path))
      absolute.relative_path_from(Pathname.new(output_dir)).to_s
    end

    def slug_case(case_id)
      case_id.to_s.gsub(/[^A-Za-z0-9_-]+/, "-")
    end
  end
end
