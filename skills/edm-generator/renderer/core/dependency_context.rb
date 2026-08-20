require "yaml"

module PilotRenderer
  class DependencyContext
    attr_reader :root, :pilot_id, :brief, :standard, :templates, :modules,
                :selection_rules, :composition_rules, :standard_markdown, :visual_rhythm

    def initialize(root:, pilot_id:)
      @root = root
      @pilot_id = pilot_id
      @brief = load_yaml("pilot/#{pilot_id}/campaign_brief.yaml")
      @standard = load_yaml("standards/edm_design_rules_v1.0.yaml")
      @templates = load_yaml("design_system/templates_v1.0.yaml")
      @modules = load_yaml("design_system/modules_v1.0.yaml")
      @selection_rules = load_yaml("design_system/template_selection_rules_v1.0.yaml")
      @composition_rules = load_yaml("design_system/module_composition_rules_v1.0.yaml")
      @standard_markdown = load_text("standards/edm_design_standard_v1.0.md")
      @visual_rhythm = load_text("design_system/visual_rhythm_rules_v1.0.md")
    end

    def assert_matches!(template:, module_ids: [])
      raise "#{pilot_id} campaign brief mismatch" unless brief.fetch("pilot_id") == pilot_id
      raise "#{pilot_id} template mismatch" unless brief.fetch("selected_template") == template
      raise "Design Standard v1.0 is not Frozen" unless frozen?(standard)
      raise "Template Library v1.0 is not Frozen" unless frozen?(templates)
      raise "Module Library v1.0 is not Frozen" unless frozen?(modules)

      template_ids = templates.fetch("templates").map { |item| item.fetch("template_id") }
      raise "Unknown frozen template: #{template}" unless template_ids.include?(template)

      known_modules = modules.fetch("modules").map { |item| item.fetch("module_id") }
      unknown_modules = module_ids - known_modules
      raise "Unknown frozen modules: #{unknown_modules.join(', ')}" unless unknown_modules.empty?

      true
    end

    def template_record(template_id)
      templates.fetch("templates").find { |item| item.fetch("template_id") == template_id }
    end

    def template_family_name(template_id)
      record = template_record(template_id)
      family = templates.fetch("template_families").find do |item|
        item.fetch("family_id") == record.fetch("template_family_id")
      end
      family.fetch("family_name")
    end

    private

    def frozen?(document)
      document.fetch("status").to_s.casecmp("frozen").zero?
    end

    def load_yaml(relative_path)
      path = File.join(root, relative_path)
      raise "Missing renderer dependency: #{path}" unless File.file?(path)

      YAML.load_file(path)
    end

    def load_text(relative_path)
      path = File.join(root, relative_path)
      raise "Missing renderer dependency: #{path}" unless File.file?(path)

      File.read(path)
    end
  end
end
